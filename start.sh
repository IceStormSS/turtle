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
  echo "❌ BOT_TOKEN не задан — бот не сможет работать."
  echo "   Railway → сервис → Variables → New Variable: BOT_TOKEN = <токен от @BotFather>"
  echo "   Затем Deployments → Redeploy. Файл .env на сервере не нужен."
  echo "   Веб-сервер всё равно поднимем, чтобы можно было посмотреть /api/health и логи."
fi

if [ -n "${DB_PATH:-}" ]; then
  echo "   DB_PATH=${DB_PATH}"
elif [ -d /data ]; then
  # Volume уже подключён, но переменную забыли — берём постоянный путь сами,
  # иначе прогресс стирается при каждом перезапуске контейнера.
  export DB_PATH=/data/turtlelingo.db
  echo "   DB_PATH не задан, но найден Volume /data — использую ${DB_PATH}"
  echo "   (лучше явно: Variables → DB_PATH=/data/turtlelingo.db)"
elif [ -n "${RAILWAY_ENVIRONMENT:-}" ]; then
  echo "⚠️ DB_PATH не задан: база ляжет внутрь контейнера и сотрётся при следующем деплое."
  echo "   Лечится так: Service → Volumes → Add Volume, Mount Path = /data,"
  echo "   затем Variables: DB_PATH=/data/turtlelingo.db"
else
  echo "   DB_PATH не задан — локальный режим, база в папке проекта"
fi

python -u app.py &
WEB_PID=$!

# Даём веб-серверу занять порт, чтобы bot.py не поднимал второй на том же порту.
sleep 3

# Бота держим в супервизоре: если он упадёт, перезапустим его, но НЕ уроним
# веб-сервис. Иначе любой сбой бота делает деплой неудачным, и Railway
# оставляет старую сборку (и сайт выглядит «необновлённым»).
(
  while true; do
    python -u bot.py
    STATUS=$?
    echo "⚠️ bot.py завершился (код $STATUS) — перезапуск через 10 с"
    sleep 10
  done
) &
BOT_PID=$!

# Сервис живёт, пока жив веб-сервер (его и проверяет healthcheck).
wait "$WEB_PID"
STATUS=$?

echo "⚠️ Веб-сервер завершился (код $STATUS) — перезапуск сервиса"
kill "$WEB_PID" "$BOT_PID" 2>/dev/null || true
wait 2>/dev/null || true
exit 1
