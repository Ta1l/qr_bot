# your_bot/handlers/states.py

"""
Модуль с FSM состояниями для управления диалогом.
Здесь определяются все возможные состояния, в которых может находиться пользователь.
"""
from typing import Optional
from aiogram.fsm.state import State, StatesGroup, State


class TestStates(StatesGroup):
    """Группа состояний для прохождения теста"""
    citizenship_question = State()
    card_blocks_question = State()
    phone_number_question = State()

    # <-- ВОТ ИЗМЕНЕНИЕ
    @classmethod
    def get_by_state_str(cls, state_str: str) -> Optional[State]:
        """
        Возвращает объект состояния по его строковому представлению.
        Например, по "TestStates:citizenship_question" вернет TestStates.citizenship_question.
        """
        # __states__ - это специальный атрибут StatesGroup, содержащий все состояния
        for state_obj in cls.__states__:
            if state_obj.state == state_str:
                return state_obj
        return None


class AdminStates(StatesGroup):
    """Группа состояний для админ-панели"""
    choosing_user = State()  # Состояние выбора пользователя для просмотра информации