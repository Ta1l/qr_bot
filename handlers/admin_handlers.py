# your_bot/handlers/admin_handlers.py

"""
Обработчики для команд администратора.
"""
import logging
import re
from datetime import datetime

from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext

from .filters import IsAdmin
from .states import AdminStates
from .keyboards import get_users_keyboard
from database.db_manager import get_all_results, get_result_by_id

logger = logging.getLogger(__name__)
admin_router = Router(name="admin_router")

# Применяем фильтр IsAdmin ко всем обработчикам в этом роутере
admin_router.message.filter(IsAdmin())


@admin_router.message(Command("all"), StateFilter(None))
async def show_all_users(message: Message, state: FSMContext):
    """
    Обработчик команды /all.
    Получает всех пользователей из БД и предлагает выбрать одного.
    """
    all_users = await get_all_results()
    
    if not all_users:
        await message.answer("В базе данных пока нет записей.")
        return

    await message.answer(
        "Выберите пользователя для просмотра информации:",
        reply_markup=get_users_keyboard(all_users)
    )
    await state.set_state(AdminStates.choosing_user)


@admin_router.message(F.text == "Отмена", StateFilter(AdminStates.choosing_user))
async def cancel_user_choice(message: Message, state: FSMContext):
    """Обработчик отмены выбора пользователя."""
    await message.answer("Действие отменено.", reply_markup=ReplyKeyboardRemove())
    await state.clear()


@admin_router.message(StateFilter(AdminStates.choosing_user))
async def show_user_info(message: Message, state: FSMContext):
    """
    Обрабатывает выбор пользователя из клавиатуры и показывает по нему информацию.
    """
    match = re.search(r"\(ID: (\d+)\)", message.text)
    if not match:
        await message.answer("Пожалуйста, выберите пользователя с помощью кнопок.")
        return

    record_id = int(match.group(1))
    user_data = await get_result_by_id(record_id)

    if not user_data:
        await message.answer("Не удалось найти информацию по данному пользователю.", reply_markup=ReplyKeyboardRemove())
        await state.clear()
        return

    # Форматируем дату для красивого вывода
    try:
        completion_date = datetime.fromisoformat(user_data['completion_date']).strftime('%Y-%m-%d %H:%M:%S')
    except (TypeError, ValueError):
        completion_date = "N/A"
        
    # Формируем красивый ответ с новыми полями
    response_text = (
        f"<b>ℹ️ Информация по пользователю {user_data.get('username', 'N/A')} (ID: {user_data.get('user_id')})</b>\n\n"
        f"<b>Имя:</b> {user_data.get('name') or 'Не указано'}\n"
        f"<b>Гражданство РФ:</b> {user_data.get('citizenship') or 'Не указано'}\n"
        f"<b>Аресты по картам:</b> {user_data.get('card_arrests') or 'Не указано'}\n"
        f"<b>Номер телефона:</b> <code>{user_data.get('phone_number') or 'Не указан'}</code>\n\n"
        f"<b>Дата прохождения:</b> {completion_date}"
    )

    await message.answer(response_text, reply_markup=ReplyKeyboardRemove(), parse_mode="HTML")
    await state.clear()