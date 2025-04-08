# main.py

import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import Command
from config import BOT_TOKEN
from handlers import user_handlers, admin_handlers

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
dp.bot = bot

user_handlers.register_user_handlers(dp)
admin_handlers.register_admin_handlers(dp)


async def help_command(message: types.Message):
    help_text = """
Функционал Бота:
/nav - Навигационное меню.
/profile - Отображает ваш профиль.
/support - Связь с администратором.
/admin - Админ панель
"""
    await message.answer(help_text)


dp.message.register(help_command, Command("help"))



async def support_command(message: types.Message):
    # Замените на актуальную информацию об администраторе
    from utils.utils import is_admin  # импортируем локально, чтобы избежать циклического импорта
    if is_admin(message.from_user.id):
        await message.answer(f"Вы администратор. Используйте админ-панель")
    else:
        admin_username = "@your_admin_username"  # Замените
        await message.answer(f"Если у вас возникли вопросы, свяжитесь с администратором: {admin_username}")


dp.message.register(support_command, Command("support"))


async def main():
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
