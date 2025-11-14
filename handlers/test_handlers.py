# your_bot/handlers/test_handlers.py

"""
Обработчики для прохождения теста.
Используют конфигурационно-управляемый подход из test_flow.py.
"""
import logging

from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext

from .states import TestStates
from .utils import finish_test, validate_phone_number
from .test_flow import TEST_FLOW, VALIDATION_RULES, FAILURE_ANSWERS

logger = logging.getLogger(__name__)
test_router = Router(name="test_router")


@test_router.callback_query(F.data == "start_test")
async def start_test_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Обработчик нажатия на кнопку "Пройти тест".
    Запускает первый шаг теста из конфигурации.
    """
    first_step_state = TestStates.citizenship_question
    step_config = TEST_FLOW[first_step_state]

    await callback.message.answer(
        text=step_config["text"],
        reply_markup=step_config["keyboard"]()
    )
    await state.set_state(first_step_state)
    await callback.answer()
    logger.info(f"Пользователь {callback.from_user.id} (@{callback.from_user.username}) начал тест")


@test_router.message(
    StateFilter(TestStates.citizenship_question, TestStates.card_blocks_question),
    lambda msg: VALIDATION_RULES[TestStates.citizenship_question](msg) or VALIDATION_RULES[TestStates.card_blocks_question](msg)
)
async def process_test_answer(message: Message, state: FSMContext, bot: Bot):
    """
    УНИВЕРСАЛЬНЫЙ обработчик для всех шагов теста типа "Да/Нет".
    """
    current_state_str = await state.get_state()
    current_state = TestStates.get_by_state_str(current_state_str) # Получаем объект состояния
    
    answer = message.text
    step_config = TEST_FLOW[current_state]
    
    # Сохраняем данные
    state_key = current_state.state.split(':')[-1].replace('_question', '')
    await state.update_data(
        {state_key: answer},
        user_id=message.from_user.id,
        username=message.from_user.username or "Без username"
    )
    logger.info(f"Пользователь {message.from_user.id} на шаге '{state_key}' ответил: {answer}")

    # Проверяем, является ли ответ "провальным"
    if answer == FAILURE_ANSWERS.get(current_state):
        failure_config = step_config["failure_path"]
        await message.answer(failure_config["message"], reply_markup=ReplyKeyboardRemove())
        await finish_test(message.from_user.id, state, bot)
        return

    # Если ответ успешный, переходим к следующему шагу
    next_step_state = step_config["success_path"]
    next_step_config = TEST_FLOW[next_step_state]
    
    await message.answer(
        text=next_step_config["text"],
        reply_markup=next_step_config["keyboard"]()
    )
    await state.set_state(next_step_state)


@test_router.message(StateFilter(TestStates.phone_number_question))
async def process_phone_number(message: Message, state: FSMContext, bot: Bot) -> None:
    """
    Обработчик получения номера телефона (оставлен отдельным из-за уникальной логики).
    """
    phone_number = None
    if message.contact:
        phone_number = message.contact.phone_number
    elif message.text and validate_phone_number(message.text):
        phone_number = message.text
    else:
        await message.answer(
            "Номер телефона введен некорректно. Пожалуйста, введите корректный номер "
            "в формате +79991234567 или используйте кнопку."
        )
        return

    await state.update_data(phone_number=phone_number)
    logger.info(f"Пользователь {message.from_user.id} предоставил номер: {phone_number}")
    
    await message.answer(
        "✅ Спасибо! Тест успешно завершен.\nВаши данные отправлены на проверку.",
        reply_markup=ReplyKeyboardRemove()
    )
    await finish_test(message.from_user.id, state, bot)


@test_router.message(StateFilter(TestStates.citizenship_question, TestStates.card_blocks_question))
async def invalid_yes_no_answer(message: Message) -> None:
    """Обработчик некорректного ответа (не 'Да'/'Нет')."""
    await message.answer("Пожалуйста, используйте кнопки 'Да' или 'Нет' для ответа.")