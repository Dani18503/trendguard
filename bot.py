"""
TrendGuard - Entrypoint principal
Envia un mensaje de prueba al canal de Telegram.
"""
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

import config
from notifier import send_message_sync


log_dir = Path(__file__).parent / "logs"
log_dir.mkdir(exist_ok=True)
log_file = log_dir / "bot.log"

handler = RotatingFileHandler(
    log_file, maxBytes=5_000_000, backupCount=3, encoding="utf-8"
)
handler.setFormatter(
    logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
)

console = logging.StreamHandler(sys.stdout)
console.setFormatter(
    logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
)

logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL, logging.INFO),
    handlers=[handler, console]
)

logger = logging.getLogger("trendguard")


def run():
    logger.info("TrendGuard iniciando...")

    mensaje = (
        "TrendGuard esta vivo\n"
        "\n"
        "Symbol: " + config.SYMBOL + "\n"
        "Timeframe: " + config.TIMEFRAME + "\n"
        "Leverage: " + str(config.LEVERAGE) + "x\n"
        "Modo: " + config.MODE + "\n"
        "Testnet: " + str(config.BINANCE_TESTNET) + "\n"
        "\n"
        "Primer mensaje de prueba. Todo en orden."
    )

    exito = send_message_sync(mensaje)

    if exito:
        logger.info("Test completado con exito")
        return 0
    logger.error("Test fallo")
    return 1


if __name__ == "__main__":
    sys.exit(run())
