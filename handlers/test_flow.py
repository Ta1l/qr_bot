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
    TestStates.citizenship_question: {
        "text": "Вы имеете Российское гражданство?",
        "keyboard": get_yes_no_keyboard,
        "success_path": TestStates.card_blocks_question, # Куда идти при ответе 'Да'
        "failure_path": {
            "message": "К сожалению, данный сервис доступен только для граждан РФ.\nТест завершен."
        }
    },
    TestStates.card_blocks_question: {
        "text": "У вас есть блокировки по картам?",
        "keyboard": get_yes_no_keyboard,
        "success_path": TestStates.phone_number_question, # Куда идти при ответе 'Нет'
        "failure_path": {
            "message": "К сожалению, мы не можем работать с заблокированными картами.\nТест завершен."
        }
    },
    TestStates.phone_number_question: {
        "text": (
            "Пожалуйста, предоставьте ваш номер телефона.\n"
            "Вы можете нажать кнопку ниже или ввести номер вручную."
        ),
        "keyboard": get_phone_keyboard
        # У этого шага нет success/failure path, т.к. он обрабатывается отдельно
    }
}

# Определяем правила валидации для каждого шага.
# Это позволяет нам иметь один универсальный обработчик для некорректных ответов.
VALIDATION_RULES = {
    TestStates.citizenship_question: F.text.in_(["Да", "Нет"]),
    TestStates.card_blocks_question: F.text.in_(["Да", "Нет"]),
}

# Определяем, какой ответ на каком шаге считается "провальным" (failure)
# Это сделано для гибкости, если на каком-то шаге 'Да' будет означать провал.
FAILURE_ANSWERS = {
    TestStates.citizenship_question: "Нет",
    TestStates.card_blocks_question: "Да",
}