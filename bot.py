"""TurtleLingo — Telegram-бот для изучения английского в стиле Duolingo.

Запуск:  python bot.py
Токен бота берётся из файла .env (строка BOT_TOKEN=...).
Поддерживает выбор вариантов кнопками, а также ввод ответов от руки прямо в чат!
"""

import html
import logging
import os
import random
import re
import socket
import sqlite3
import sys
import threading
import time
from datetime import date, timedelta

import requests

from grammar import QUESTIONS_BY_TIER, check_grammar_answer, normalize_answer
from tunnel import get_saved_webapp_url, run_tunnel_thread
from words import LEVEL_NAMES, POOLS

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LESSON_SIZE = 20  # слов в одном уроке

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("turtlelingo")

WEBAPP_URL = get_saved_webapp_url()


# ---------------------------------------------------------------- настройки
def load_env():
    path = os.path.join(BASE_DIR, ".env")
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_env()
TOKEN = os.environ.get("BOT_TOKEN", "").strip()
if not TOKEN or "вставь" in TOKEN.lower():
    print("Не найден BOT_TOKEN. Создай файл .env и впиши туда: BOT_TOKEN=твой_токен")
    sys.exit(1)

API = f"https://api.telegram.org/bot{TOKEN}"
http = requests.Session()


def api(method, **params):
    try:
        r = http.post(f"{API}/{method}", json=params, timeout=45)
        data = r.json()
        if not data.get("ok"):
            log.warning("Telegram %s: %s", method, data.get("description"))
        return data
    except Exception as e:
        log.warning("Ошибка сети (%s): %s", method, e)
        return {}


def esc(text):
    return html.escape(str(text))


def send(chat_id, text, kb=None):
    params = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if kb is not None:
        params["reply_markup"] = kb
    data = api("sendMessage", **params)
    return data.get("result", {}).get("message_id")


def edit(chat_id, message_id, text, kb=None):
    params = {"chat_id": chat_id, "message_id": message_id, "text": text, "parse_mode": "HTML"}
    if kb:
        params["reply_markup"] = kb
    data = api("editMessageText", **params)
    if not data.get("ok") and "not modified" not in str(data.get("description", "")):
        return send(chat_id, text, kb)
    return message_id


# ---------------------------------------------------------------- база данных
db = sqlite3.connect(os.path.join(BASE_DIR, "turtlelingo.db"), check_same_thread=False)
db.row_factory = sqlite3.Row
db.executescript(
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


def ensure_user(uid, name="Друг"):
    with db:
        db.execute("INSERT OR IGNORE INTO users(id, name) VALUES(?, ?)", (uid, name))
    return db.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()


def learned_keys(uid):
    return {r["key"] for r in db.execute("SELECT key FROM learned WHERE user_id=?", (uid,))}


# ---------------------------------------------------------------- тексты и кнопки
BTN_LEARN = "🐢 Учиться"
BTN_PROFILE = "👤 Профиль"
BTN_TEST = "🧪 Тест уровня"


def get_webapp_url():
    global WEBAPP_URL
    if not WEBAPP_URL:
        WEBAPP_URL = get_saved_webapp_url()
    return WEBAPP_URL


def get_menu_keyboard():
    url = get_webapp_url()
    keyboard = []
    if url:
        # Кнопка открытия Mini App прямо внутри Telegram с иконкой WebApp
        keyboard.append([{"text": "📱 Открыть приложение", "web_app": {"url": url}}])
    keyboard.append([{"text": BTN_LEARN}, {"text": BTN_PROFILE}])
    keyboard.append([{"text": BTN_TEST}])
    return {"keyboard": keyboard, "resize_keyboard": True}


def get_start_inline():
    url = get_webapp_url()
    rows = []
    if url:
        rows.append([{"text": "📱 Открыть приложение", "web_app": {"url": url}}])
    rows.append([{"text": "🆕 Я совсем с нуля (A0)", "callback_data": "lvl0"}])
    rows.append([{"text": "🧪 Пройти тест уровня (с окончаниями)", "callback_data": "test"}])
    rows.append([{"text": "🎯 Выбрать уровень самому", "callback_data": "choose_lvl"}])
    return {"inline_keyboard": rows}


# Для обратной совместимости — удалено. MENU больше не нужен как глобал.
# Все вызовы используют get_menu_keyboard() напрямую.


PRAISE = [
    "Правильно! 🎉",
    "Отлично! 🐢💚",
    "Так держать! 🔥",
    "Верно! Ты молодец! 👏",
    "Супер! Всё точно 🐢",
    "Точно в цель! 💪",
    "Великолепно! ⭐",
]
ENCOURAGE = [
    "Почти! Ошибки — это часть учёбы 💚",
    "Ничего страшного, ты запомнишь! 🐢",
    "Не сдавайся! Шаг за шагом мы дойдём до цели 🐢",
    "Бывает! Разберём и пойдём дальше 💪",
]


def inline(rows):
    return {"inline_keyboard": [[{"text": t, "callback_data": d}] for t, d in rows]}


def inline_grid(rows_of_tuples):
    return {"inline_keyboard": [[{"text": t, "callback_data": d} for t, d in row] for row in rows_of_tuples]}


def options_kb(options, dont_know=False):
    rows = [(o, f"a:{i}") for i, o in enumerate(options)]
    if dont_know:
        rows.append(("🤷 Не знаю (пропустить)", "a:-1"))
    return inline(rows)


def progress_bar(done, total):
    k = round(10 * done / total) if total else 0
    return "🟩" * k + "⬜" * (10 - k) + f"  {done}/{total}"


# ---------------------------------------------------------------- упражнения
def distractors(word, field, n=3, same_pos=False):
    pool = POOLS[word["pool"]]
    cands = [w for w in pool if w["key"] != word["key"]]
    if same_pos:
        same = [w for w in cands if w["pos"] == word["pos"]]
        if len(same) >= n:
            cands = same
    random.shuffle(cands)
    out, seen = [], {word[field]}
    for w in cands:
        if w[field] not in seen:
            out.append(w[field])
            seen.add(w[field])
        if len(out) == n:
            break
    return out


def make_exercise(word, kind):
    if kind == "en2ru":
        text = f"Как переводится слово <b>{esc(word['en'])}</b>?"
        correct = word["ru"]
        options = [correct] + distractors(word, "ru")
    elif kind == "ru2en":
        text = f"Как по-английски: <b>{esc(word['ru'])}</b>?"
        correct = word["en"]
        options = [correct] + distractors(word, "en")
    else:  # gap
        text = (
            "Вставь пропущенное слово в предложение:\n\n"
            f"<b>{esc(word['sent'])}</b>\n\n"
            f"💡 Подсказка: {esc(word['ru'])}"
        )
        correct = word["en"]
        options = [correct] + distractors(word, "en", same_pos=True)
    random.shuffle(options)
    return {"text": text, "options": options, "correct": options.index(correct), "word": word}


# ---------------------------------------------------------------- сессии (в памяти)
sessions = {}


def expired(chat_id):
    send(chat_id, "Этот урок уже закрыт. Нажми «🐢 Учиться», чтобы начать заново.", get_menu_keyboard())


# ---------------------------------------------------------------- профиль
def show_profile(u, chat_id):
    count = len(learned_keys(u["id"]))
    total = sum(len(p) for p in POOLS.values())
    text = (
        f"👤 <b>Профиль: {esc(u['name'])}</b>\n\n"
        f"🎓 Уровень английского: <b>{LEVEL_NAMES[u['level']]}</b>\n"
        f"📚 Выучено слов: <b>{count}</b> из {total}\n"
        f"⭐ Опыт (XP): <b>{u['xp']}</b>\n"
        f"🔥 Серия дней: <b>{u['streak']}</b>"
    )
    rows = []
    url = get_webapp_url()
    if url:
        rows.append([{"text": "📱 Открыть приложение", "web_app": {"url": url}}])
    rows.append([{"text": "✏️ Выбрать уровень вручную", "callback_data": "choose_lvl"}])
    rows.append([{"text": "🧪 Пройти тест уровня", "callback_data": "test"}])
    send(chat_id, text, {"inline_keyboard": rows})


def show_level_selector(chat_id):
    text = (
        "🎯 <b>Выбери свой уровень английского:</b>\n\n"
        "• <b>A0</b> — С самого нуля\n"
        "• <b>A1</b> — Базовый (Present Simple, -s, -ing)\n"
        "• <b>A2</b> — Элементарный (Past Simple -ed, сравнения -er/-est)\n"
        "• <b>B1</b> — Средний (Present Perfect, -ly, предлоги)\n"
        "• <b>B2</b> — Выше среднего (суффиксы -ment, -able, деепричастия)"
    )
    kb = inline_grid([
        [("🥚 A0", "set_lvl:0"), ("🐣 A1", "set_lvl:1"), ("🐢 A2", "set_lvl:2")],
        [("🌿 B1", "set_lvl:3"), ("🏆 B2", "set_lvl:4")],
    ])
    send(chat_id, text, kb)


# ---------------------------------------------------------------- старт и выбор уровня
def ask_level(chat_id, name):
    text = (
        f"🐢 Привет, {esc(name)}! Я <b>TurtleLingo</b> — интерактивное приложение для изучения английского прямо в Telegram.\n\n"
        "Учимся регулярно и без стресса: слова, грамматические окончания и предложения с пропусками.\n\n"
        "Открывай приложение кнопкой ниже или выбирай действие 👇"
    )
    send(chat_id, text, get_start_inline())


def start_learning(u, chat_id):
    if not u["tested"]:
        ask_level(chat_id, u["name"])
    else:
        start_lesson(u, chat_id)


# ---------------------------------------------------------------- тест уровня
def start_test(u, chat_id):
    qs = []
    # По 2 вопроса на грамматику и окончания + 1 на слово в контексте для каждого уровня (A1, A2, B1, B2)
    for tier in range(1, 5):
        tier_grammar = QUESTIONS_BY_TIER.get(tier, [])
        for g in random.sample(tier_grammar, min(2, len(tier_grammar))):
            opts = list(g["options"])
            correct_val = opts[g["correct_idx"]]
            random.shuffle(opts)
            qs.append({
                "tier": tier,
                "kind": "grammar",
                "grammar_data": g,
                "ex": {
                    "text": (
                        f"📐 <b>{esc(g['title'])}</b>\n\n"
                        f"{esc(g['question'])}\n\n"
                        f"Предложение: <b>{esc(g['sentence'])}</b>"
                    ),
                    "options": opts,
                    "correct": opts.index(correct_val),
                },
            })

        # 1 вопрос на слово в контексте
        word = random.choice(POOLS[tier])
        ex = make_exercise(word, "gap")
        qs.append({
            "tier": tier,
            "kind": "vocab",
            "word": word,
            "ex": ex,
        })

    s = {"mode": "test", "qs": qs, "idx": 0, "score": {1: 0, 2: 0, 3: 0, 4: 0}, "msg": None}
    sessions[u["id"]] = s
    send(
        chat_id,
        "🧪 <b>Тест уровня: грамматика + окончания + слова</b>\n\n"
        "Будет до 12 вопросов (по 3 на каждый уровень). Мы проверяем окончания (-ed, -s, -ing, -er) и формы слов, "
        "чтобы точно определить твой уровень!\n\n"
        "💡 <i>Отвечать можно кнопками или писать ответ от руки прямо в чат!</i>",
        # Без клавиатуры — Telegram сам скрывает кнопки во время прохождения теста
    )
    show_test_question(u["id"], chat_id, new_message=True)


def show_test_question(uid, chat_id, new_message=False):
    s = sessions.get(uid)
    if not s or s["mode"] != "test":
        return
    q = s["qs"][s["idx"]]
    current = s["idx"] + 1
    total = len(s["qs"])

    badge = f"Уровень A{q['tier']}" if q["tier"] < 3 else f"Уровень B{q['tier'] - 2}"
    kind_lbl = "Грамматика и окончания" if q["kind"] == "grammar" else "Слово в контексте"

    text = (
        f"🧪 <b>Тест уровня</b> — вопрос {current}/{total}\n"
        f"🏷 <i>{badge} • {kind_lbl}</i>\n\n"
        f"{q['ex']['text']}\n\n"
        "<i>✍️ Нажми кнопку с вариантом или напиши ответ в чат:</i>"
    )
    kb = options_kb(q["ex"]["options"], dont_know=True)
    if new_message or not s.get("msg"):
        s["msg"] = send(chat_id, text, kb)
    else:
        s["msg"] = edit(chat_id, s["msg"], text, kb)


def answer_test(uid, chat_id, choice):
    s = sessions.get(uid)
    if not s or s["mode"] != "test":
        expired(chat_id)
        return

    q = s["qs"][s["idx"]]
    is_correct = False
    explanation = ""

    if choice == -1:
        # Пропуск
        is_correct = False
        explanation = "Вопрос пропущен."
    elif q["kind"] == "grammar":
        g = q["grammar_data"]
        is_correct, explanation = check_grammar_answer(g, choice)
    else:
        # Словарный вопрос
        w = q["word"]
        if isinstance(choice, int):
            is_correct = (choice == q["ex"]["correct"])
        else:
            norm = normalize_answer(str(choice))
            target_en = normalize_answer(w["en"])
            target_ru = normalize_answer(w["ru"])
            ru_variants = [normalize_answer(p) for p in re.split(r"[,;/]+", w["ru"])]
            is_correct = (norm == target_en) or (norm == target_ru) or (norm in ru_variants)
        explanation = f"<b>{esc(w['en'])}</b> — {esc(w['ru'])}\nПример: {esc(w['sent'])}"

    if choice != -1 and is_correct:
        s["score"][q["tier"]] += 1

    s["idx"] += 1
    answered = s["idx"]
    tier = q["tier"]
    tier_finished = (answered % 3 == 0)

    # Завершаем тест, если ответили на все или если не набрали минимум 2 из 3 на текущем этапе
    should_stop = (answered >= len(s["qs"])) or (tier_finished and s["score"][tier] < 2)

    # Краткий промежуточный отклик с пояснением правила
    status_icon = "✅ Верно!" if is_correct else "💡 Пояснение:"
    feedback_text = f"{status_icon}\n{explanation}"
    send(chat_id, feedback_text)

    if should_stop:
        finish_test(uid, chat_id)
    else:
        show_test_question(uid, chat_id, new_message=True)


def finish_test(uid, chat_id):
    s = sessions.pop(uid, None)
    if not s:
        return

    level = 0
    for tier in range(1, 5):
        if s["score"][tier] >= 2:
            level = tier
        else:
            break

    pool = 0 if level == 0 else min(level + 1, 4)
    with db:
        db.execute("UPDATE users SET level=?, pool=?, tested=1 WHERE id=?", (level, pool, uid))

    plans = {
        0: "Начнём с самого начала — простые слова и приветствия! 🐣",
        1: "Базовый уровень (A1). Закрепим Present Simple, местоимения и базовые окончания! 💪",
        2: "Элементарный уровень (A2). Ты отлично справляешься с базой и прошедшим временем -ed! Будем развивать фразы 🐢",
        3: "Средний уровень (B1). Уверенная грамматика! Будем расширять лексику для свободных бесед 🌿",
        4: "Выше среднего (B2). Отличные знания сложных суффиксов и конструкций! 🚀",
    }
    plan = plans.get(level, plans[2])

    breakdown = "\n".join(
        f"• Уровень {t}: {s['score'][t]}/3 {'✅' if s['score'][t] >= 2 else '⚪'}"
        for t in range(1, 5)
    )

    text = (
        f"🎉 <b>Тест уровня завершён!</b>\n\n"
        f"Твой подтверждённый уровень: <b>{LEVEL_NAMES[level]}</b>\n\n"
        f"Результаты по этапам:\n{breakdown}\n\n"
        f"{plan}\n\n"
        f"<i>Ты всегда можешь изменить уровень в любой момент в «👤 Профиль».</i>"
    )
    send(chat_id, text, get_menu_keyboard())


# ---------------------------------------------------------------- урок
def pick_words(u):
    learned = learned_keys(u["id"])
    words = []
    for p in range(u["pool"], 5):
        for w in POOLS[p]:
            if w["key"] not in learned:
                words.append(w)
                if len(words) == LESSON_SIZE:
                    return words, False
    review = not words
    if len(words) < LESSON_SIZE:
        chosen = {w["key"] for w in words}
        extra = [
            w
            for p in range(max(u["pool"] - 1, 0), 5)
            for w in POOLS[p]
            if w["key"] not in chosen
        ]
        words += random.sample(extra, min(LESSON_SIZE - len(words), len(extra)))
    return words, review


KINDS = ["en2ru", "gap", "ru2en"]


def start_lesson(u, chat_id):
    words, review = pick_words(u)
    queue = [{"word": w, "kind": KINDS[i % 3], "retry": False} for i, w in enumerate(words)]

    # Добавляем также упражнения на окончания для закрепления
    tier = max(1, min(u["level"], 4))
    tier_grammar = QUESTIONS_BY_TIER.get(tier, QUESTIONS_BY_TIER[2])
    for g in random.sample(tier_grammar, min(3, len(tier_grammar))):
        queue.append({
            "word": None,
            "kind": "grammar",
            "grammar_data": g,
            "retry": False,
        })
    random.shuffle(queue)

    s = {
        "mode": "lesson",
        "words": words,
        "queue": queue,
        "cur": None,
        "xp": 0,
        "ok": 0,
        "done": 0,
        "total": len(queue),
        "msg": None,
    }
    sessions[u["id"]] = s
    lines = "\n".join(
        f"{i}. <b>{esc(w['en'])}</b> — {esc(w['ru'])}" for i, w in enumerate(words[:10], 1)
    )
    title = "🔁 Повторяем слова" if review else "🐢 Слова и упражнения на сегодня"
    text = (
        f"{title}:\n\n{lines}\n\n"
        "<i>Прочитай, запомни, и начнём упражнения! Отвечать можно кнопками или писать ответ в чат.</i>"
    )
    s["msg"] = send(chat_id, text, inline([("🚀 Поехали!", "go")]))


def show_question(uid, chat_id, new_message=False):
    s = sessions.get(uid)
    if not s or s["mode"] != "lesson":
        return
    if not s["queue"]:
        finish_lesson(uid, chat_id)
        return

    item = s["queue"].pop(0)
    if item["kind"] == "grammar":
        g = item["grammar_data"]
        opts = list(g["options"])
        correct_val = opts[g["correct_idx"]]
        random.shuffle(opts)
        ex = {
            "text": (
                f"📐 <b>{esc(g['title'])}</b>\n\n"
                f"{esc(g['question'])}\n\n"
                f"Предложение: <b>{esc(g['sentence'])}</b>"
            ),
            "options": opts,
            "correct": opts.index(correct_val),
        }
    else:
        ex = make_exercise(item["word"], item["kind"])

    s["cur"] = {"item": item, "ex": ex}
    text = (
        f"{progress_bar(s['done'], s['total'])}\n\n"
        f"{ex['text']}\n\n"
        "<i>✍️ Выбери кнопку или напиши ответ в чат:</i>"
    )
    kb = options_kb(ex["options"])
    if new_message or not s.get("msg"):
        s["msg"] = send(chat_id, text, kb)
    else:
        s["msg"] = edit(chat_id, s["msg"], text, kb)


def answer_lesson(uid, chat_id, choice):
    s = sessions.get(uid)
    if not s or s["mode"] != "lesson" or not s.get("cur"):
        expired(chat_id)
        return

    item, ex = s["cur"]["item"], s["cur"]["ex"]
    s["cur"] = None
    is_correct = False
    explanation = ""

    if item["kind"] == "grammar":
        g = item["grammar_data"]
        is_correct, explanation = check_grammar_answer(g, choice)
    else:
        word = item["word"]
        if isinstance(choice, int):
            is_correct = (choice == ex["correct"])
        else:
            norm = normalize_answer(str(choice))
            target_en = normalize_answer(word["en"])
            target_ru = normalize_answer(word["ru"])
            ru_vars = [normalize_answer(p) for p in re.split(r"[,;/]+", word["ru"])]
            is_correct = (norm == target_en) or (norm == target_ru) or (norm in ru_vars)
        sentence = esc(word["sent"]).replace("___", f"<b>{esc(word['en'])}</b>")
        explanation = f"{sentence}\n<b>{esc(word['en'])}</b> — {esc(word['ru'])}"

    note = ""
    if is_correct:
        s["xp"] += 5 if item["retry"] else 10
        if not item["retry"]:
            s["ok"] += 1
        s["done"] += 1
        head = random.choice(PRAISE)
    else:
        correct_text = ex["options"][ex["correct"]]
        head = random.choice(ENCOURAGE) + f"\nПравильный ответ: <b>{esc(correct_text)}</b>"
        if item["retry"]:
            s["done"] += 1
        else:
            item["retry"] = True
            s["queue"].append(item)
            note = "\n\n🔁 Это задание повторим в конце урока."

    text = f"{head}\n\n{explanation}{note}"
    button = "Дальше ➡️" if s["queue"] else "Завершить 🏁"
    send(chat_id, text, inline([(button, "next")]))


def finish_lesson(uid, chat_id):
    s = sessions.pop(uid, None)
    if not s:
        return
    u = ensure_user(uid)

    with db:
        for w in s.get("words", []):
            if w and "key" in w:
                db.execute("INSERT OR IGNORE INTO learned(user_id, key) VALUES(?, ?)", (uid, w["key"]))

    learned = learned_keys(uid)
    level, pool, old_level = u["level"], u["pool"], u["level"]
    while all(w["key"] in learned for w in POOLS[pool]):
        if pool >= 1:
            level = max(level, pool)
        if pool < 4:
            pool += 1
        else:
            break

    today = date.today()
    streak = u["streak"]
    if u["last_day"] != today.isoformat():
        yesterday = (today - timedelta(days=1)).isoformat()
        streak = streak + 1 if u["last_day"] == yesterday else 1

    with db:
        db.execute(
            "UPDATE users SET level=?, pool=?, xp=xp+?, streak=?, last_day=? WHERE id=?",
            (level, pool, s["xp"], streak, today.isoformat(), uid),
        )

    text = (
        "🎉 <b>Урок завершён!</b>\n\n"
        f"✅ С первого раза верно: <b>{s['ok']}</b> из {s['total']}\n"
        f"⭐ Получено XP: <b>+{s['xp']}</b>\n"
        f"🔥 Серия дней: <b>{streak}</b>\n"
        f"📚 Всего выучено слов: <b>{len(learned)}</b>"
    )
    if level > old_level:
        text += f"\n\n🏆 <b>Новый уровень: {LEVEL_NAMES[level]}!</b>"
    text += "\n\nОтличная работа! Возвращайся за следующей порцией 🐢"
    send(chat_id, text, inline([("➕ Ещё один урок", "more")]))


# ---------------------------------------------------------------- обработка событий
def on_message(m):
    text = m.get("text", "").strip()
    uid = m["from"]["id"]
    chat_id = m["chat"]["id"]
    u = ensure_user(uid, m["from"].get("first_name", "Друг"))

    # Системные кнопки меню и команды имеют наивысший приоритет
    MENU_BUTTONS = (BTN_LEARN, BTN_PROFILE, BTN_TEST)
    if text in MENU_BUTTONS or text.startswith("/"):
        sessions.pop(uid, None)
        if text.startswith("/start") or text.startswith("/menu"):
            if u["tested"]:
                url = get_webapp_url()
                rows = []
                if url:
                    rows.append([{"text": "📱 Открыть приложение", "web_app": {"url": url}}])
                rows.append([{"text": "🧪 Тест уровня", "callback_data": "test"}, {"text": "🐢 Учиться", "callback_data": "more"}])
                rows.append([{"text": "👤 Профиль", "callback_data": "profile_btn"}])
                send(
                    chat_id,
                    f"🐢 С возвращением, {esc(u['name'])}! Выбирай, что делаем 👇",
                    {"inline_keyboard": rows},
                )
            else:
                ask_level(chat_id, u["name"])
        elif text == BTN_LEARN:
            start_learning(u, chat_id)
        elif text == BTN_PROFILE:
            show_profile(u, chat_id)
        elif text == BTN_TEST:
            start_test(u, chat_id)
        elif text.startswith("/level"):
            show_level_selector(chat_id)
        else:
            send(chat_id, "Выбирай действие кнопками внизу 👇", get_menu_keyboard())
        return

    # Если пользователь сейчас проходит тест или урок — проверяем ввод от руки:
    if uid in sessions:
        s = sessions[uid]
        if s["mode"] == "test":
            answer_test(uid, chat_id, text)
            return
        elif s["mode"] == "lesson" and s.get("cur"):
            answer_lesson(uid, chat_id, text)
            return

    send(chat_id, "Выбирай действие кнопками внизу 👇", get_menu_keyboard())


def on_callback(cb):
    api("answerCallbackQuery", callback_query_id=cb["id"])
    uid = cb["from"]["id"]
    data = cb.get("data", "")
    chat_id = cb["message"]["chat"]["id"]
    mid = cb["message"]["message_id"]
    u = ensure_user(uid, cb["from"].get("first_name", "Друг"))

    if data == "lvl0":
        with db:
            db.execute("UPDATE users SET level=0, pool=0, tested=1 WHERE id=?", (uid,))
        edit(chat_id, mid, "Отлично! Начнём с самого начала — это совсем не страшно 🐣")
        send(chat_id, "Нажми «🐢 Учиться», и я дам первые слова!", get_menu_keyboard())
    elif data == "profile_btn":
        show_profile(u, chat_id)
    elif data == "test":
        start_test(u, chat_id)
    elif data == "choose_lvl":
        show_level_selector(chat_id)
    elif data.startswith("set_lvl:"):
        lvl = int(data.split(":")[1])
        pool = 0 if lvl == 0 else min(lvl + 1, 4)
        with db:
            db.execute("UPDATE users SET level=?, pool=?, tested=1 WHERE id=?", (lvl, pool, uid))
        send(chat_id, f"🎯 Твой уровень успешно обновлён на: <b>{LEVEL_NAMES[lvl]}</b>!", get_menu_keyboard())
    elif data in ("more",):
        start_lesson(ensure_user(uid), chat_id)
    elif data in ("go", "next"):
        s = sessions.get(uid)
        if not s or s["mode"] != "lesson":
            expired(chat_id)
        elif s.get("cur") is None:
            show_question(uid, chat_id, new_message=True)
    elif data.startswith("a:"):
        s = sessions.get(uid)
        if not s:
            expired(chat_id)
            return
        choice = int(data[2:])
        if s["mode"] == "test":
            answer_test(uid, chat_id, choice)
        elif s["cur"] is not None:
            answer_lesson(uid, chat_id, choice)


def main():
    me = api("getMe")
    if not me.get("ok"):
        print("Не удалось подключиться к Telegram. Проверь токен в .env и интернет.")
        sys.exit(1)
    log.info("Бот запущен: @%s", me["result"]["username"])

    # 1. Запуск локального веб-сервера на порту 5000 (если ещё не запущен)
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            port_busy = (s.connect_ex(("127.0.0.1", 5000)) == 0)
        if not port_busy:
            import app
            log.info("Запуск локального веб-сервера TurtleLingo на порту 5000...")
            t_app = threading.Thread(target=app.start_web_server, args=(5000,), daemon=True)
            t_app.start()
            time.sleep(0.5)
    except Exception as e:
        log.warning("Ошибка проверки/запуска веб-сервера: %s", e)

    # 2. Регистрация кнопки меню Telegram WebApp (рядом с полем ввода)
    url = get_webapp_url()
    if url:
        api("setChatMenuButton", menu_button={"type": "web_app", "text": "Приложение", "web_app": {"url": url}})

    def on_tunnel_ready(ready_url):
        global WEBAPP_URL
        WEBAPP_URL = ready_url
        log.info("✅ Telegram WebApp подключён: %s", ready_url)
        api("setChatMenuButton", menu_button={"type": "web_app", "text": "Приложение", "web_app": {"url": ready_url}})

    # 3. Запуск SSH-туннеля для получения HTTPS ссылки для Telegram WebApp
    run_tunnel_thread(port=5000, on_url_ready=on_tunnel_ready)

    offset = None
    while True:
        params = {"timeout": 30, "allowed_updates": ["message", "callback_query"]}
        if offset:
            params["offset"] = offset
        data = api("getUpdates", **params)
        if not data.get("ok"):
            time.sleep(3)
            continue
        for upd in data["result"]:
            offset = upd["update_id"] + 1
            try:
                if "message" in upd:
                    on_message(upd["message"])
                elif "callback_query" in upd:
                    on_callback(upd["callback_query"])
            except Exception:
                log.exception("Ошибка при обработке обновления")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Бот остановлен.")
