# your_bot/handlers/utils.py

"""
Вспомогательные функции для обработчиков.
Содержит логику формирования результатов, валидации и другие утилиты.
"""

import json
import logging
import re
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from typing import Dict, Any # <-- ВОТ ЭТА СТРОКА БЫЛА ПРОПУЩЕНА

from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramAPIError

from config import ADMIN_IDS
from database.db_manager import save_test_result

logger = logging.getLogger(__name__)


async def notify_admins(bot: Bot, state_data: Dict[str, Any]) -> None:
    """
    Отправляет отформатированный результат теста всем администраторам.
    """
    if not ADMIN_IDS:
        logger.warning("Переменная ADMIN_IDS пуста. Уведомления не будут отправлены.")
        return

    completion_time = datetime.now(timezone.utc).astimezone(ZoneInfo("Europe/Moscow")).strftime('%Y-%m-%d %H:%M:%S')
    
    text = (
        f"✅ <b>Новый результат теста</b>\n\n"
        f"<b>Пользователь:</b> @{state_data.get('username', 'N/A')} (ID: {state_data.get('user_id')})\n"
        f"<b>Имя:</b> {state_data.get('name', 'Не указано')}\n"
        f"<b>Гражданство РФ:</b> {state_data.get('citizenship', 'Не указано')}\n"
        f"<b>Аресты по картам:</b> {state_data.get('card_arrests', 'Не указано')}\n"
        f"<b>Телефон:</b> <code>{state_data.get('phone_number', 'Не указан')}</code>\n\n"
        f"<b>Время завершения (МСК):</b> {completion_time}"
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

# ... (остальной код файла остается без изменений) ...

async def finish_test(user_id: int, state: FSMContext, bot: Bot) -> None:
    data = await state.get_data()
    logger.info(f"Завершение теста для пользователя {user_id}. Данные: {data}")
    await save_test_result(data)
    print_test_result(data)
    await notify_admins(bot, data)
    await state.clear()


def print_test_result(result: Dict[str, Any]) -> None:
    json_result = json.dumps(result, ensure_ascii=False, indent=2)
    print("\n" + "="*50)
    print("РЕЗУЛЬТАТ ТЕСТА (сохранен в БД):")
    print("="*50)
    print(json_result)
    print("="*50 + "\n")


def validate_phone_number(phone: str) -> bool:
    cleaned_phone = re.sub(r'\D', '', phone)
    if len(cleaned_phone) == 11 and cleaned_phone.startswith(('7', '8')):
        return True
    elif len(cleaned_phone) == 10:
        return True
    return False