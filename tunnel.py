"""Модуль для автоматического создания HTTPS туннеля для Telegram WebApp (Mini App).

Использует встроенный OpenSSH клиента Windows (ssh.exe) и сервис localhost.run,
чтобы бесплатно и без регистрации получить валидный HTTPS URL, необходимый Telegram.
"""

import logging
import os
import re
import subprocess
import threading
import time

log = logging.getLogger("turtlelingo.tunnel")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
URL_FILE = os.path.join(BASE_DIR, "webapp_url.txt")


def get_saved_webapp_url():
    """Возвращает сохраненный URL туннеля, если он есть."""
    # Сначала проверяем переменную окружения
    env_url = os.environ.get("WEBAPP_URL", "").strip()
    if env_url.startswith("https://"):
        return env_url

    # Затем файл webapp_url.txt
    if os.path.exists(URL_FILE):
        try:
            with open(URL_FILE, "r", encoding="utf-8") as f:
                url = f.read().strip()
                if url.startswith("https://"):
                    return url
        except Exception:
            pass
    return None


def run_tunnel_thread(port=5000, on_url_ready=None):
    """Запускает SSH туннель в отдельном потоке и перезапускает его при обрыве."""
    def _worker():
        while True:
            cmd = [
                "ssh",
                "-o", "StrictHostKeyChecking=no",
                "-o", "ServerAliveInterval=30",
                "-o", "ServerAliveCountMax=3",
                "-R", f"80:127.0.0.1:{port}",
                "nokey@localhost.run",
            ]
            try:
                log.info("Запуск SSH туннеля к localhost.run...")
                proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                )
                url_found = False
                for line in proc.stdout:
                    line = line.strip()
                    if line:
                        log.debug("SSH: %s", line)
                    m = re.search(r"https://[a-zA-Z0-9-]+\.lhr\.life", line)
                    if m and not url_found:
                        url = m.group(0)
                        url_found = True
                        log.info("✅ Telegram WebApp HTTPS URL: %s", url)
                        try:
                            with open(URL_FILE, "w", encoding="utf-8") as f:
                                f.write(url)
                        except Exception as e:
                            log.warning("Не удалось сохранить URL: %s", e)
                        if on_url_ready:
                            try:
                                on_url_ready(url)
                            except Exception as e:
                                log.error("Ошибка в on_url_ready: %s", e)
                proc.wait()
            except Exception as e:
                log.warning("Ошибка SSH туннеля: %s. Переподключение через 5 сек...", e)
            time.sleep(5)

    t = threading.Thread(target=_worker, daemon=True)
    t.start()
    return t


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    print("Запуск туннеля...")
    run_tunnel_thread(port=5000)
    while True:
        time.sleep(1)
