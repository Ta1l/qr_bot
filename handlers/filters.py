"""
Кастомные фильтры для обработчиков.
"""
from aiogram.filters import BaseFilter
from aiogram.types import Message
from config import ADMIN_IDS

class IsAdmin(BaseFilter):
    """
    Фильтр для проверки, является ли пользователь администратором бота.
    """
    async def __call__(self, message: Message) -> bool:
        return message.from_user.id in ADMIN_IDS