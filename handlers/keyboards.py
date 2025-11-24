# your_bot/handlers/keyboards.py

"""
Модуль с клавиатурами для бота.
Централизованное хранение всех клавиатур упрощает их переиспользование и модификацию.
"""

from typing import List, Dict, Any
from aiogram.types import (
    ReplyKeyboardMarkup, 
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from aiogram.utils.keyboard import ReplyKeyboardBuilder


def get_start_test_keyboard() -> InlineKeyboardMarkup:
    """
    Инлайн клавиатура с кнопкой начала теста.
    Используется в приветственном сообщении.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🚀 Поехали!",
                    callback_data="start_test"
                )
            ]
        ]
    )


def get_yes_no_keyboard(placeholder: str = "Выберите ответ") -> ReplyKeyboardMarkup:
    """
    Стандартная клавиатура Да/Нет.
    Переиспользуется для разных вопросов.
    
    Args:
        placeholder: Текст-подсказка в поле ввода.
    """
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="Да"),
                KeyboardButton(text="Нет")
            ]
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder=placeholder
    )


def get_phone_keyboard() -> ReplyKeyboardMarkup:
    """
    Клавиатура для запроса номера телефона.
    Содержит кнопку быстрой отправки контакта.
    """
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="📱 Отправить номер телефона",
                    request_contact=True
                )
            ]
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder="Нажмите кнопку или введите номер"
    )


def get_users_keyboard(users: List[Dict[str, Any]]) -> ReplyKeyboardMarkup:
    """
    Создает Reply-клавиатуру со списком пользователей для администратора.
    
    Args:
        users: Список словарей с данными пользователей (id, username).
    """
    # Используем билдер для динамического создания клавиатуры
    builder = ReplyKeyboardBuilder()
    
    for user in users:
        # Текст кнопки содержит и ник, и ID из базы для уникальности
        builder.button(text=f"{user['username']} (ID: {user['id']})")
    
    # Добавляем кнопку "Отмена" для выхода из состояния выбора
    builder.button(text="Отмена")
    
    # Выстраиваем кнопки в один столбец для лучшей читаемости
    builder.adjust(1)
    
    return builder.as_markup(
        resize_keyboard=True, 
        one_time_keyboard=True,
        input_field_placeholder="Выберите пользователя из списка"
    )