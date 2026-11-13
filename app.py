"""TurtleLingo — веб-приложение для изучения английского.

Запуск: python app.py
Открывает веб-интерфейс в браузере (по умолчанию http://localhost:5000).
Работает со стандартной библиотекой Python (без обязательных сторонних фреймворков).
"""

import http.server
import json
import logging
import os
import random
import re
import socketserver
import sqlite3
import sys
import urllib.parse
import webbrowser
from datetime import date, timedelta

from grammar import (
    GRAMMAR_TOPICS,
    QUESTIONS_BY_TIER,
    check_grammar_answer,
    normalize_answer,
)
from words import LEVEL_NAMES, POOLS

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")
DB_PATH = os.path.join(BASE_DIR, "turtlelingo.db")
PORT = 5000

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("turtlelingo_web")


# ---------------------------------------------------------------- База данных
def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY,
            name TEXT,
            level INTEGER DEFAULT 2,
            pool INTEGER DEFAULT 2,
            xp INTEGER DEFAULT 0,
            streak INTEGER DEFAULT 0,
            last_day TEXT,
            tested INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS learned(
            user_id INTEGER,
            key TEXT,
            PRIMARY KEY(user_id, key)
        );
        """
    )
    return conn


db = get_db()


def get_current_user():
    # Берём первого пользователя или создаём по умолчанию
    row = db.execute("SELECT * FROM users ORDER BY id ASC LIMIT 1").fetchone()
    if not row:
        with db:
            db.execute(
                "INSERT INTO users(id, name, level, pool, xp, streak, tested) VALUES(1, 'Друг', 2, 2, 0, 0, 0)"
            )
        row = db.execute("SELECT * FROM users WHERE id=1").fetchone()
    return dict(row)


def get_learned_count(user_id):
    row = db.execute("SELECT COUNT(*) as cnt FROM learned WHERE user_id=?", (user_id,)).fetchone()
    return row["cnt"] if row else 0


def get_all_words_flat():
    all_words = []
    for lvl, word_list in POOLS.items():
        all_words.extend(word_list)
    return all_words


# ---------------------------------------------------------------- Генерация заданий
def make_vocab_test_exercise(word):
    # Вопрос по слову с предложением
    correct = word["ru"]
    pool = POOLS[word["pool"]]
    distractors = [w["ru"] for w in pool if w["key"] != word["key"] and w["ru"] != correct]
    random.shuffle(distractors)
    options = [correct] + distractors[:3]
    random.shuffle(options)

    # Принимаемые варианты ввода от руки
    accepted = [
        word["ru"].lower(),
        word["en"].lower(),
    ]
    # Добавляем синонимы через запятую если есть
    for part in re.split(r"[,;/]+", word["ru"]):
        clean = part.strip().lower()
        if clean:
            accepted.append(clean)

    return {
        "id": f"vocab_{word['key']}",
        "tier": word["pool"],
        "level_name": f"A{word['pool']}" if word["pool"] < 3 else f"B{word['pool'] - 2}",
        "category": "vocab",
        "title": f"Слово: {word['en']}",
        "question": f"Как переводится слово «{word['en']}»?",
        "sentence": word["sent"],
        "options": options,
        "correct_idx": options.index(correct),
        "target_word": word["en"],
        "accepted": accepted,
        "explanation": f"«{word['en']}» переводится как «{word['ru']}». Пример: {word['sent']}",
    }


def generate_placement_test():
    """Формирует тест из 12 вопросов: по 2 на грамматические окончания + 1 на слово в контексте для каждого уровня (A1, A2, B1, B2)."""
    questions = []
    for tier in range(1, 5):
        # 2 вопроса на грамматику и окончания
        tier_grammar = QUESTIONS_BY_TIER.get(tier, [])
        sampled_grammar = random.sample(tier_grammar, min(2, len(tier_grammar)))
        for g in sampled_grammar:
            # Создаем копию с перемешанными вариантами
            opts = list(g["options"])
            correct_val = opts[g["correct_idx"]]
            random.shuffle(opts)
            new_idx = opts.index(correct_val)

            questions.append({
                "id": g["id"],
                "tier": tier,
                "level_name": g["level_name"],
                "category": "grammar",
                "title": g["title"],
                "question": g["question"],
                "sentence": g["sentence"],
                "options": opts,
                "correct_idx": new_idx,
                "target_ending": g["target_ending"],
                "target_full": g.get("target_full", ""),
                "accepted": g["accepted"],
                "explanation": g["explanation"],
            })

        # 1 вопрос на слово в контексте
        word = random.choice(POOLS[tier])
        questions.append(make_vocab_test_exercise(word))

    return questions


def generate_lesson_for_user(user):
    user_id = user["id"]
    pool_idx = min(user["pool"], 4)

    # Изученные ключи
    learned = {r["key"] for r in db.execute("SELECT key FROM learned WHERE user_id=?", (user_id,))}

    words = []
    for p in range(pool_idx, 5):
        for w in POOLS[p]:
            if w["key"] not in learned:
                words.append(w)
                if len(words) == 16:
                    break
        if len(words) == 16:
            break

    if len(words) < 16:
        # Добираем из доступных
        extra = [w for p in range(0, 5) for w in POOLS[p] if w not in words]
        words.extend(random.sample(extra, min(16 - len(words), len(extra))))

    # Формируем упражнения
    queue = []
    kinds = ["en2ru", "gap", "ru2en"]

    for i, w in enumerate(words):
        kind = kinds[i % 3]
        if kind == "en2ru":
            correct = w["ru"]
            cands = [x["ru"] for x in POOLS[w["pool"]] if x["ru"] != correct]
            random.shuffle(cands)
            opts = [correct] + cands[:3]
            random.shuffle(opts)
            ex = {
                "question": f"Как переводится слово «{w['en']}»?",
                "sentence": w["sent"],
                "options": opts,
                "correct": opts.index(correct),
            }
        elif kind == "ru2en":
            correct = w["en"]
            cands = [x["en"] for x in POOLS[w["pool"]] if x["en"] != correct]
            random.shuffle(cands)
            opts = [correct] + cands[:3]
            random.shuffle(opts)
            ex = {
                "question": f"Как по-английски «{w['ru']}»?",
                "sentence": w["sent"],
                "options": opts,
                "correct": opts.index(correct),
            }
        else:  # gap
            correct = w["en"]
            same_pos = [x["en"] for x in POOLS[w["pool"]] if x["pos"] == w["pos"] and x["en"] != correct]
            if len(same_pos) < 3:
                same_pos = [x["en"] for x in POOLS[w["pool"]] if x["en"] != correct]
            random.shuffle(same_pos)
            opts = [correct] + same_pos[:3]
            random.shuffle(opts)
            ex = {
                "question": "Вставь пропущенное слово в предложение:",
                "sentence": w["sent"],
                "options": opts,
                "correct": opts.index(correct),
            }

        queue.append({
            "word": w,
            "kind": kind,
            "ex": ex,
            "retry": False,
        })

    # Добавляем 4 упражнения на грамматические окончания соответствующего уровня
    tier = max(1, min(user["level"], 4))
    tier_grammar = QUESTIONS_BY_TIER.get(tier, QUESTIONS_BY_TIER[2])
    for g in random.sample(tier_grammar, min(4, len(tier_grammar))):
        opts = list(g["options"])
        correct_val = opts[g["correct_idx"]]
        random.shuffle(opts)
        queue.append({
            "word": None,
            "kind": "grammar",
            "ex": {
                "id": g["id"],
                "question": g["question"],
                "sentence": g["sentence"],
                "options": opts,
                "correct": opts.index(correct_val),
                "target_full": g.get("target_full", ""),
                "target_ending": g["target_ending"],
                "accepted": g["accepted"],
                "explanation": g["explanation"],
            },
            "retry": False,
        })

    random.shuffle(queue)
    return words, queue


# ---------------------------------------------------------------- HTTP Обработчик
class TurtleHandler(http.server.SimpleHTTPRequestHandler):
    def send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        url = urllib.parse.urlparse(self.path)
        path = url.path

        if path == "/" or path == "/index.html":
            file_path = os.path.join(TEMPLATES_DIR, "index.html")
            try:
                with open(file_path, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
            except Exception as e:
                self.send_error(404, f"File not found: {e}")
            return

        elif path.startswith("/static/"):
            filename = path[len("/static/"):]
            file_path = os.path.join(STATIC_DIR, filename)
            if os.path.exists(file_path) and os.path.isfile(file_path):
                ext = os.path.splitext(filename)[1].lower()
                mime = "text/plain"
                if ext == ".css":
                    mime = "text/css; charset=utf-8"
                elif ext == ".js":
                    mime = "application/javascript; charset=utf-8"
                elif ext in (".png", ".jpg", ".jpeg"):
                    mime = f"image/{ext[1:]}"
                elif ext == ".svg":
                    mime = "image/svg+xml"

                with open(file_path, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", mime)
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
                return

        # ================= REST API =================
        if path == "/api/user":
            params = urllib.parse.parse_qs(url.query)
            user_id = params.get("id", [None])[0]
            if user_id:
                try:
                    row = db.execute("SELECT * FROM users WHERE id=?", (int(user_id),)).fetchone()
                    if row:
                        u = dict(row)
                        u["learned_count"] = get_learned_count(u["id"])
                        u["total_words"] = len(get_all_words_flat())
                        self.send_json(u)
                        return
                except Exception:
                    pass

            u = get_current_user()
            learned_cnt = get_learned_count(u["id"])
            total_words = len(get_all_words_flat())
            u["learned_count"] = learned_cnt
            u["total_words"] = total_words
            self.send_json(u)
            return

        elif path == "/api/test/start":
            questions = generate_placement_test()
            self.send_json({"questions": questions})
            return

        elif path == "/api/lesson/start":
            u = get_current_user()
            words, queue = generate_lesson_for_user(u)
            self.send_json({"words": words, "queue": queue})
            return

        elif path == "/api/dictionary":
            all_words = get_all_words_flat()
            self.send_json(all_words)
            return

        elif path == "/api/grammar":
            self.send_json(GRAMMAR_TOPICS)
            return

        self.send_error(404, "Endpoint not found")

    def do_POST(self):
        url = urllib.parse.urlparse(self.path)
        path = url.path
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
        try:
            payload = json.loads(body)
        except Exception:
            payload = {}

        if path == "/api/user/sync":
            uid = payload.get("id")
            name = payload.get("name", "Друг")
            if uid:
                with db:
                    db.execute(
                        "INSERT OR IGNORE INTO users(id, name, level, pool, xp, streak, tested) VALUES(?, ?, 2, 2, 0, 0, 0)",
                        (uid, name),
                    )
                    db.execute("UPDATE users SET name=? WHERE id=?", (name, uid))
                row = db.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
                u = dict(row)
                u["learned_count"] = get_learned_count(uid)
                u["total_words"] = len(get_all_words_flat())
                self.send_json({"ok": True, "user": u})
                return

        if path == "/api/user/set-level":
            new_level = int(payload.get("level", 2))
            new_pool = 0 if new_level == 0 else min(new_level + 1, 4)
            u = get_current_user()
            with db:
                db.execute(
                    "UPDATE users SET level=?, pool=?, tested=1 WHERE id=?",
                    (new_level, new_pool, u["id"]),
                )
            u = get_current_user()
            u["learned_count"] = get_learned_count(u["id"])
            u["total_words"] = len(get_all_words_flat())
            self.send_json({"ok": True, "user": u})
            return

        elif path == "/api/user/reset":
            u = get_current_user()
            with db:
                db.execute("UPDATE users SET xp=0, streak=0, learned_count=0 WHERE id=?", (u["id"],))
                db.execute("DELETE FROM learned WHERE user_id=?", (u["id"],))
            u = get_current_user()
            u["learned_count"] = 0
            u["total_words"] = len(get_all_words_flat())
            self.send_json({"ok": True, "user": u})
            return

        elif path == "/api/test/check":
            q_data = payload.get("q_data", {})
            user_input = payload.get("user_input")

            category = q_data.get("category", "grammar")
            if category == "grammar":
                is_correct, explanation = check_grammar_answer(q_data, user_input)
            else:
                # Проверка словарного ответа
                if isinstance(user_input, int) or (isinstance(user_input, str) and user_input.isdigit() and len(user_input) == 1):
                    idx = int(user_input)
                    is_correct = (idx == q_data.get("correct_idx"))
                else:
                    norm = normalize_answer(str(user_input))
                    accepted = [normalize_answer(a) for a in q_data.get("accepted", [])]
                    target = normalize_answer(q_data.get("target_word", ""))
                    is_correct = (norm in accepted) or (norm == target)
                explanation = q_data.get("explanation", "")

            self.send_json({"is_correct": is_correct, "explanation": explanation})
            return

        elif path == "/api/test/finish":
            level = int(payload.get("level", 2))
            scores = payload.get("scores", {})
            u = get_current_user()
            pool = 0 if level == 0 else min(level + 1, 4)
            with db:
                db.execute(
                    "UPDATE users SET level=?, pool=?, tested=1 WHERE id=?",
                    (level, pool, u["id"]),
                )
            u = get_current_user()
            u["learned_count"] = get_learned_count(u["id"])
            u["total_words"] = len(get_all_words_flat())
            self.send_json({"ok": True, "user": u, "scores": scores})
            return

        elif path == "/api/lesson/check":
            item = payload.get("item", {})
            choice = payload.get("choice")
            ex = item.get("ex", {})

            if item.get("kind") == "grammar":
                is_correct, explanation = check_grammar_answer(ex, choice)
            else:
                if isinstance(choice, int) or (isinstance(choice, str) and choice.isdigit() and len(choice) == 1):
                    idx = int(choice)
                    is_correct = (idx == ex.get("correct"))
                else:
                    # Ввод от руки для урока
                    norm = normalize_answer(str(choice))
                    w = item.get("word", {})
                    target_en = normalize_answer(w.get("en", ""))
                    target_ru = normalize_answer(w.get("ru", ""))
                    ru_variants = [normalize_answer(p) for p in re.split(r"[,;/]+", w.get("ru", ""))]
                    is_correct = (norm == target_en) or (norm == target_ru) or (norm in ru_variants)

                w = item.get("word", {})
                explanation = f"<b>{w.get('en')}</b> — {w.get('ru')}" if w else ""

            self.send_json({"is_correct": is_correct, "explanation": explanation})
            return

        elif path == "/api/lesson/finish":
            xp_gained = int(payload.get("xp", 0))
            words = payload.get("words", [])
            u = get_current_user()
            uid = u["id"]

            with db:
                for w in words:
                    if w and "key" in w:
                        db.execute("INSERT OR IGNORE INTO learned(user_id, key) VALUES(?, ?)", (uid, w["key"]))

            today = date.today()
            streak = u["streak"]
            if u["last_day"] != today.isoformat():
                yesterday = (today - timedelta(days=1)).isoformat()
                streak = streak + 1 if u["last_day"] == yesterday else 1

            with db:
                db.execute(
                    "UPDATE users SET xp=xp+?, streak=?, last_day=? WHERE id=?",
                    (xp_gained, streak, today.isoformat(), uid),
                )

            u = get_current_user()
            u["learned_count"] = get_learned_count(uid)
            u["total_words"] = len(get_all_words_flat())
            self.send_json({"ok": True, "user": u})
            return

        self.send_error(404, "Endpoint not found")


def start_web_server(port=5000):
    server_address = ("127.0.0.1", port)

    class ReusableServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
        allow_reuse_address = True

    httpd = ReusableServer(server_address, TurtleHandler)
    log.info("TurtleLingo веб-сервер слушает на http://127.0.0.1:%s", port)
    try:
        httpd.serve_forever()
    except Exception as e:
        log.warning("Веб-сервер остановлен: %s", e)


def find_free_port(start_port=5000):
    import socket
    for port in range(start_port, start_port + 50):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("0.0.0.0", port))
                return port
            except OSError:
                continue
    return start_port


def run_server():
    port = 5000
    url = f"http://localhost:{port}"

    print("=" * 60)
    print(f"🐢 TurtleLingo Web App успешно запущено!")
    print(f"👉 Открой в браузере: {url}")
    print("=" * 60)

    try:
        webbrowser.open(url)
    except Exception:
        pass

    start_web_server(port)


if __name__ == "__main__":
    run_server()
