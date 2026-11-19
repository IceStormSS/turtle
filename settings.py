"""Общие настройки окружения — работают одинаково локально и на хостинге.

Читает .env (если есть), затем переменные окружения процесса. На хостинге
(Railway и т.п.) .env обычно нет, всё приходит через Variables.
"""

import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Логи с эмодзи и кириллицей не должны падать при перенаправлении вывода
# (Windows cp1251, Railway/Docker-логи и т.п.).
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def load_env():
    """Подхватывает значения из .env, не перетирая уже заданные переменные."""
    path = os.path.join(BASE_DIR, ".env")
    if not os.path.exists(path):
        return
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))
    except Exception:
        pass


load_env()


def env(name, default=""):
    """Значение переменной без пробелов и случайных кавычек.

    В панелях вроде Railway легко вставить BOT_TOKEN="123:abc" целиком —
    кавычки ломают запросы к Telegram, поэтому срезаем их.
    """
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().strip('"').strip("'")


# Признак «мы на хостинге»: локально ничего этого нет.
IS_HOSTED = any(
    os.environ.get(key)
    for key in (
        "RAILWAY_ENVIRONMENT",
        "RAILWAY_ENVIRONMENT_ID",
        "RAILWAY_PROJECT_ID",
        "RENDER",
        "DYNO",
        "FLY_APP_NAME",
    )
)

# Локально слушаем только localhost; на хостинге — 0.0.0.0 (иначе прокси не достучится).
HOST = env("HOST") or ("0.0.0.0" if (IS_HOSTED or env("PORT")) else "127.0.0.1")
PORT = int(env("PORT") or "5000")

# DB_PATH позволяет вынести базу на постоянный Volume (например /data/turtlelingo.db).
DB_PATH = env("DB_PATH")
if not DB_PATH:
    # На хостинге с подключённым Volume база должна лежать на нём,
    # иначе прогресс стирается при каждом перезапуске контейнера.
    if IS_HOSTED and os.path.isdir("/data"):
        DB_PATH = "/data/turtlelingo.db"
    else:
        DB_PATH = os.path.join(BASE_DIR, "turtlelingo.db")

# Туннель (localhost.run) нужен только локально. На хостинге есть свой HTTPS-домен.
DISABLE_TUNNEL = IS_HOSTED or env("DISABLE_TUNNEL").lower() in ("1", "true", "yes")

if os.path.dirname(DB_PATH):
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
