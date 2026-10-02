"""
TrendGuard - Entrypoint principal (modo servicio)
"""
import logging
import signal
import sys
import time
from logging.handlers import RotatingFileHandler
from pathlib import Path

import config
from notifier import send_message_sync


log_dir = Path(__file__).parent / "logs"
log_dir.mkdir(exist_ok=True)
log_file = log_dir / "bot.log"

handler = RotatingFileHandler(log_file, maxBytes=5_000_000, backupCount=3, encoding="utf-8")
handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))

console = logging.StreamHandler(sys.stdout)
console.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))

logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL, logging.INFO),
    handlers=[handler, console]
)

logger = logging.getLogger("trendguard")

running = True


def handle_shutdown(signum, frame):
    global running
    logger.info("Senal recibida. Cerrando TrendGuard...")
    running = False


def run():
    global running
    signal.signal(signal.SIGTERM, handle_shutdown)
    signal.signal(signal.SIGINT, handle_shutdown)

    logger.info("TrendGuard iniciando en modo servicio...")

    mensaje = (
        "TrendGuard ONLINE\n"
        "\n"
        "Symbol: " + config.SYMBOL + "\n"
        "Timeframe: " + config.TIMEFRAME + "\n"
        "Leverage: " + str(config.LEVERAGE) + "x\n"
        "Modo: " + config.MODE + "\n"
        "\n"
        "Servicio systemd activo."
    )
    send_message_sync(mensaje)

    counter = 0
    while running:
        counter += 1
        logger.info(f"TrendGuard activo - heartbeat #{counter}")
        time.sleep(60)

    logger.info("TrendGuard detenido correctamente")
    return 0


if __name__ == "__main__":
    sys.exit(run())