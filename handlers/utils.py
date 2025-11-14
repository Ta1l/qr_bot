"""
Вспомогательные функции для обработчиков.
Содержит логику формирования результатов, валидации и другие утилиты.
"""

import json
import logging
import re
from typing import Dict, Any

from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramAPIError

from config import ADMIN_IDS
from database.db_manager import save_test_result  # <-- Импортируем нашу новую функцию


logger = logging.getLogger(__name__)


async def notify_admins(bot: Bot, state_data: Dict[str, Any]) -> None:
    """
    Отправляет отформатированный результат теста всем администраторам.
    
    Args:
        bot: Экземпляр объекта Bot для отправки сообщений.
        state_data: Словарь с данными из FSM.
    """
    if not ADMIN_IDS:
        logger.warning("Переменная ADMIN_IDS пуста. Уведомления не будут отправлены.")
        return

    # Формируем красивое сообщение из данных
    text = (
        f"✅ <b>Новый результат теста</b>\n\n"
        f"<b>Пользователь:</b> @{state_data.get('username', 'N/A')} (ID: {state_data.get('user_id')})\n"
        f"<b>Гражданство РФ:</b> {state_data.get('citizenship', 'N/A')}\n"
        f"<b>Блокировки карт:</b> {state_data.get('card_blocks', 'N/A')}\n"
        f"<b>Телефон:</b> {state_data.get('phone_number', 'N/A')}"
    )

    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(
                chat_id=admin_id,
                text=text,
                parse_mode=ParseMode.HTML
            )
        except TelegramAPIError as e:
            logger.error(f"Не удалось отправить сообщение администратору {admin_id}: {e}")
        except Exception as e:
            logger.error(f"Непредвиденная ошибка при отправке сообщения администратору {admin_id}: {e}")


async def finish_test(user_id: int, state: FSMContext, bot: Bot) -> None:
    """
    Завершает тест, сохраняет результат в БД, отправляет его админам и очищает состояние.
    
    Args:
        user_id: ID пользователя, завершившего тест.
        state: Контекст FSM с сохраненными данными.
        bot: Экземпляр объекта Bot.
    """
    data = await state.get_data()
    
    # Логируем данные перед сохранением
    logger.info(f"Завершение теста для пользователя {user_id}. Данные: {data}")

    # 1. Сохраняем результат в базу данных
    await save_test_result(data)

    # 2. Выводим результат в консоль для отладки
    print_test_result(data)

    # 3. Отправляем уведомление администраторам
    await notify_admins(bot, data)
    
    # 4. Очищаем состояние пользователя
    await state.clear()


def print_test_result(result: Dict[str, Any]) -> None:
    """
    Красиво выводит результат теста в консоль.
    
    Args:
        result: Словарь с данными из FSM.
    """
    json_result = json.dumps(result, ensure_ascii=False, indent=2)
    print("\n" + "="*50)
    print("РЕЗУЛЬТАТ ТЕСТА (сохранен в БД):")
    print("="*50)
    print(json_result)
    print("="*50 + "\n")


def validate_phone_number(phone: str) -> bool:
    """
    Улучшенная проверка корректности номера телефона (российский формат).
    """
    cleaned_phone = re.sub(r'\D', '', phone)
    if len(cleaned_phone) == 11 and cleaned_phone.startswith(('7', '8')):
        return True
    elif len(cleaned_phone) == 10:
        return True
    return False