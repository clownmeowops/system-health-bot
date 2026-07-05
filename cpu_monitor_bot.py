import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
import time
import socket
import logging
from datetime import datetime

import psutil
import requests

# ---------- Настройки ----------
TOKEN = os.getenv("TG_BOT_TOKEN", "твой токен")
CHAT_ID = os.getenv("TG_CHAT_ID", "твой чат айди")

CPU_THRESHOLD = 80.0        # порог загрузки CPU в процентах
CHECK_INTERVAL = 10         # как часто проверять CPU, в секундах
ALERT_COOLDOWN = 300        # не слать повторное уведомление раньше, чем через N секунд
CPU_SAMPLE_INTERVAL = 3     # интервал усреднения при измерении CPU (psutil)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("cpu_monitor_bot")


def send_telegram_message(text: str) -> None:
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    try:
        resp = requests.post(url, data=payload, timeout=10)
        if not resp.ok:
            log.error("Ошибка отправки в Telegram: %s", resp.text)
    except requests.RequestException as e:
        log.error("Не удалось отправить сообщение в Telegram: %s", e)


def main() -> None:
    if TOKEN == "ВАШ_ТОКЕН_БОТА" or CHAT_ID == "ВАШ_CHAT_ID":
        log.warning(
            "Похоже, TOKEN и/или CHAT_ID не настроены. "
            "Задайте их в коде или через переменные окружения TG_BOT_TOKEN / TG_CHAT_ID."
        )

    hostname = socket.gethostname()
    log.info("Мониторинг CPU запущен на хосте %s. Порог: %.1f%%", hostname, CPU_THRESHOLD)

    last_alert_time = 0.0
    was_above_threshold = False

    while True:
        cpu_percent = psutil.cpu_percent(interval=CPU_SAMPLE_INTERVAL)
        now = time.time()
        log.info("Текущая загрузка CPU: %.1f%%", cpu_percent)

        if cpu_percent > CPU_THRESHOLD:
            if not was_above_threshold or (now - last_alert_time) >= ALERT_COOLDOWN:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                message = (
                    f"⚠️ <b>Высокая загрузка CPU</b>\n"
                    f"Сервер: <code>{hostname}</code>\n"
                    f"Загрузка: <b>{cpu_percent:.1f}%</b>\n"
                    f"Порог: {CPU_THRESHOLD:.0f}%\n"
                    f"Время: {timestamp}"
                )
                send_telegram_message(message)
                last_alert_time = now
            was_above_threshold = True
        else:
            was_above_threshold = False

        time.sleep(max(0, CHECK_INTERVAL - CPU_SAMPLE_INTERVAL))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log.info("Остановлено пользователем.")
