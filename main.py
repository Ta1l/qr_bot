import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from handlers import test_router, admin_router # <-- Добавляем admin_router
from handlers.keyboards import get_start_test_keyboard
from database.db_manager import init_db

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

dp = Dispatcher(storage=MemoryStorage())

# Подключаем роутеры
dp.include_router(test_router)
dp.include_router(admin_router) # <-- Подключаем новый роутер


@dp.message(Command("start"))
async def command_start_handler(message: Message) -> None:
    await message.answer(
        text="Тут приветственное сообщение!",
        reply_markup=get_start_test_keyboard(),
        parse_mode=ParseMode.HTML
    )
    logger.info(f"Пользователь {message.from_user.id} запустил бота")


async def on_startup():
    await init_db()

async def main() -> None:
    dp.startup.register(on_startup)
    bot = Bot(token=BOT_TOKEN)
    logger.info("Бот запущен и готов к работе!")
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()
        logger.info("Бот остановлен")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Получен сигнал остановки")
        sys.exit(0)