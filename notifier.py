"""
TrendGuard - Modulo de notificaciones a Telegram
"""
import logging
import asyncio
from telegram import Bot
from telegram.error import TelegramError

import config

logger = logging.getLogger(__name__)


async def send_message(text):
    try:
        bot = Bot(token=config.TELEGRAM_BOT_TOKEN)
        await bot.send_message(
            chat_id=config.TELEGRAM_CHAT_ID,
            text=text,
            parse_mode="Markdown"
        )
        logger.info("Mensaje enviado a Telegram")
        return True
    except TelegramError as e:
        logger.error("Error Telegram: " + str(e))
        return False
    except Exception as e:
        logger.error("Error inesperado: " + str(e))
        return False


def send_message_sync(text):
    return asyncio.run(send_message(text))
