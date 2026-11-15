#!/usr/bin/env bash
# Единая точка входа для Railway: веб-сервер + Telegram-бот в одном сервисе.
# Оба процесса должны видеть ОДНУ базу (DB_PATH на Volume), поэтому
# два отдельных сервиса здесь не подходят.
set -uo pipefail

PORT="${PORT:-5000}"
export PORT

echo "🐢 TurtleLingo: старт веб-сервера на 0.0.0.0:${PORT} и Telegram-бота"
echo "   DB_PATH=${DB_PATH:-<локальная папка проекта>}"

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
