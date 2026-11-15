#!/usr/bin/env bash
# Единая точка входа для Railway: веб-сервер + Telegram-бот в одном сервисе.
# Оба процесса должны видеть ОДНУ базу (DB_PATH на Volume), поэтому
# два отдельных сервиса здесь не подходят.
set -uo pipefail

PORT="${PORT:-5000}"
export PORT

echo "🐢 TurtleLingo: старт веб-сервера на 0.0.0.0:${PORT} и Telegram-бота"

# --- проверки конфигурации: лучше упасть сразу с понятным текстом ---
if [ -z "${BOT_TOKEN:-}" ]; then
  echo "❌ BOT_TOKEN не задан."
  echo "   Railway → сервис → Variables → New Variable: BOT_TOKEN = <токен от @BotFather>"
  echo "   Затем Deployments → Redeploy. Файл .env на сервере не нужен."
  exit 1
fi

if [ -n "${DB_PATH:-}" ]; then
  echo "   DB_PATH=${DB_PATH}"
elif [ -n "${RAILWAY_ENVIRONMENT:-}" ]; then
  echo "⚠️ DB_PATH не задан: база ляжет внутрь контейнера и сотрётся при следующем деплое."
  echo "   Лечится так: Service → Volumes → Add Volume, Mount Path = /data,"
  echo "   затем Variables: DB_PATH=/data/turtlelingo.db"
else
  echo "   DB_PATH не задан — локальный режим, база в папке проекта"
fi

python app.py &
WEB_PID=$!

# Даём веб-серверу занять порт, чтобы bot.py не поднимал второй на том же порту.
sleep 3

python bot.py &
BOT_PID=$!

# Ждём завершения любого из процессов и валим сервис целиком,
# чтобы Railway перезапустил оба — иначе останется «полуживой» контейнер.
wait -n "$WEB_PID" "$BOT_PID"
STATUS=$?

echo "⚠️ Один из процессов завершился (код $STATUS) — перезапуск сервиса"
kill "$WEB_PID" "$BOT_PID" 2>/dev/null || true
wait 2>/dev/null || true
exit 1
