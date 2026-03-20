"""
Главный файл — запускает Telegram бота.
"""

import logging
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import config
from handlers import start, chat, image

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("bot")


async def main():
    log.info("🚀 Запуск бота...")
    log.info(f"   Модель: {config.GROQ_MODEL}")
    log.info(f"   Админы: {config.ADMIN_IDS}")

    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    # Порядок важен: start первым, потом chat (он ловит все текстовые сообщения)
    dp.include_router(start.router)
    dp.include_router(image.router)
    dp.include_router(chat.router)

    await bot.delete_webhook(drop_pending_updates=True)
    log.info("✅ Бот запущен! Напиши /start в Telegram.")

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        log.info("👋 Бот остановлен")


if __name__ == "__main__":
    asyncio.run(main())
