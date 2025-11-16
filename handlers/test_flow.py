# your_bot/handlers/test_flow.py

"""
Конфигурация и логика прохождения теста.
Этот файл описывает каждый шаг теста в виде структуры данных,
что позволяет легко изменять вопросы, порядок и логику ветвления.
"""
from aiogram import F

from .states import TestStates
from .keyboards import get_yes_no_keyboard, get_phone_keyboard

# Описываем весь флоу теста в виде словаря.
# Ключ - текущее состояние FSM.
TEST_FLOW = {
    # ШАГ 1: Вопрос об имени
    TestStates.name_question: {
        "type": "text", # Указываем, что ожидаем произвольный текст
        "text": "Как вас зовут?",
        "keyboard": None, # Клавиатура не нужна
        "success_path": TestStates.citizenship_question,
    },
    
    # ШАГ 2: Вопрос о гражданстве
    TestStates.citizenship_question: {
        "type": "yes_no", # Указываем тип вопроса
        "text": "Есть ли у Вас Российское гражданство?",
        "keyboard": get_yes_no_keyboard,
        "success_path": TestStates.card_arrests_question, # Куда идти при ответе 'Да'
        "failure_path": { # Что делать при ответе 'Нет'
            "message": "Извините, предложение только для обладателей Российского гражданства."
        }
    },

    # ШАГ 3: Вопрос об арестах
    TestStates.card_arrests_question: {
        "type": "yes_no",
        "text": "Есть ли у вас аресты по картам?",
        "keyboard": get_yes_no_keyboard,
        "success_path": TestStates.phone_number_question, # В любом случае идем дальше
        "special_cases": { # Специальный обработчик для ответа 'Да'
            "Да": {
                "message": "Аресты это не проблема, служба поддержки подскажет как избежать ограничений."
            }
        }
    },

    # ШАГ 4: Вопрос о номере телефона
    TestStates.phone_number_question: {
        "type": "phone", # Уникальный тип для телефона
        "text": (
            "Пожалуйста, предоставьте ваш номер телефона.\n"
            "Вы можете нажать кнопку ниже или ввести номер вручную."
        ),
        "keyboard": get_phone_keyboard
    }
}

# Определяем правила валидации для каждого шага.
VALIDATION_RULES = {
    TestStates.citizenship_question: F.text.in_(["Да", "Нет"]),
    TestStates.card_arrests_question: F.text.in_(["Да", "Нет"]),
    # Для имени и телефона валидация встроена в их обработчики
}

# Определяем, какой ответ на каком шаге считается "провальным" (завершает тест)
FAILURE_ANSWERS = {
    TestStates.citizenship_question: "Нет",
    # У вопроса об арестах теперь нет провального ответа
}