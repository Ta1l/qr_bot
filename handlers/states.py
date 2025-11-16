# your_bot/handlers/states.py

"""
Модуль с FSM состояниями для управления диалогом.
Здесь определяются все возможные состояния, в которых может находиться пользователь.
"""
from typing import Optional
from aiogram.fsm.state import State, StatesGroup


class TestStates(StatesGroup):
    """Группа состояний для прохождения теста"""
    name_question = State()                 # НОВЫЙ: Вопрос об имени
    citizenship_question = State()
    card_arrests_question = State()         # ПЕРЕИМЕНОВАН: Вопрос об арестах
    phone_number_question = State()

    @classmethod
    def get_by_state_str(cls, state_str: str) -> Optional[State]:
        """
        Возвращает объект состояния по его строковому представлению.
        """
        for state_obj in cls.__states__:
            if state_obj.state == state_str:
                return state_obj
        return None


class AdminStates(StatesGroup):
    """Группа состояний для админ-панели"""
    choosing_user = State()