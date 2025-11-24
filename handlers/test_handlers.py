# your_bot/handlers/test_handlers.py

"""
Обработчики для прохождения теста.
Используют конфигурационно-управляемый подход из test_flow.py.
"""
import logging

from aiogram import Router, F, Bot, types
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State

from .states import TestStates
from .utils import finish_test, validate_phone_number
from .test_flow import TEST_FLOW, FAILURE_ANSWERS

logger = logging.getLogger(__name__)
test_router = Router(name="test_router")


async def proceed_to_next_step(message: Message, state: FSMContext, next_state: State):
    """Хелпер-функция для перехода к следующему шагу теста."""
    step_config = TEST_FLOW[next_state]
    keyboard = step_config.get("keyboard")
    
    await message.answer(
        text=step_config["text"],
        reply_markup=keyboard() if keyboard else ReplyKeyboardRemove()
    )
    await state.set_state(next_state)


@test_router.callback_query(F.data == "start_test")
async def start_test_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Обработчик нажатия на кнопку "Пройти тест".
    Запускает первый шаг теста из новой конфигурации.
    """
    first_step_state = TestStates.name_question
    await proceed_to_next_step(callback.message, state, first_step_state)
    await callback.answer()
    logger.info(f"Пользователь {callback.from_user.id} (@{callback.from_user.username}) начал тест")


@test_router.message(StateFilter(TestStates.name_question), F.text)
async def process_name_answer(message: Message, state: FSMContext):
    """Обработчик ответа на вопрос об имени."""
    await state.update_data(
        name=message.text,
        user_id=message.from_user.id,
        username=message.from_user.username or "Без username"
    )
    logger.info(f"Пользователь {message.from_user.id} ввел имя: {message.text}")

    current_config = TEST_FLOW[TestStates.name_question]
    await proceed_to_next_step(message, state, current_config["success_path"])


@test_router.message(
    StateFilter(TestStates.citizenship_question, TestStates.card_arrests_question),
    F.text.in_(["Да", "Нет"])
)
async def process_yes_no_answer(message: Message, state: FSMContext, bot: Bot):
    """
    УНИВЕРСАЛЬНЫЙ обработчик для всех шагов теста типа "Да/Нет".
    """
    current_state_str = await state.get_state()
    current_state = TestStates.get_by_state_str(current_state_str)
    
    if not current_state:
        logger.error(f"Ошибка: не удалось определить состояние для {current_state_str}")
        return

    answer = message.text
    step_config = TEST_FLOW[current_state]
    
    state_key = current_state.state.split(':')[-1].replace('_question', '')
    await state.update_data({state_key: answer})
    logger.info(f"Пользователь {message.from_user.id} на шаге '{state_key}' ответил: {answer}")

    if answer == FAILURE_ANSWERS.get(current_state):
        failure_config = step_config["failure_path"]
        await message.answer(failure_config["message"], reply_markup=ReplyKeyboardRemove())
        await finish_test(message.from_user.id, state, bot)
        return

    special_cases = step_config.get("special_cases", {})
    if answer in special_cases:
        await message.answer(special_cases[answer]["message"])

    await proceed_to_next_step(message, state, step_config["success_path"])


# ===> ИЗМЕНЕНИЯ ЗДЕСЬ <===
@test_router.message(StateFilter(TestStates.phone_number_question))
async def process_phone_number(message: Message, state: FSMContext, bot: Bot) -> None:
    """Обработчик получения номера телефона."""
    phone_number = None
    if message.contact:
        phone_number = message.contact.phone_number
    elif message.text and validate_phone_number(message.text):
        phone_number = message.text
    else:
        await message.answer(
            "Номер телефона введен некорректно. Пожалуйста, введите корректный номер."
        )
        return

    await state.update_data(phone_number=phone_number)
    logger.info(f"Пользователь {message.from_user.id} предоставил номер: {phone_number}")
    
    # 1. Формируем новое финальное сообщение
    registration_link_placeholder = "(ссылка на регистрацию)"
    instruction_link = "https://clck.ru/3QMBsz"
    support_user_placeholder = "@Lavka_Job_Support"

    final_text = (
        f"✅ Тест пройден! Вот Ваша ссылка на регистрацию - {registration_link_placeholder}.\n\n"
        f"Инструкция по регистрации - {instruction_link}.\n"
        f"Поддержка - {support_user_placeholder}."
    )
    
    # 2. Отправляем его пользователю
    await message.answer(final_text, reply_markup=ReplyKeyboardRemove(), parse_mode=None)

    # 3. Завершаем тест (отправляем данные админу и т.д.)
    await finish_test(message.from_user.id, state, bot)


@test_router.message(StateFilter(TestStates.citizenship_question, TestStates.card_arrests_question))
async def invalid_yes_no_answer(message: Message) -> None:
    """Обработчик некорректного ответа (не 'Да'/'Нет')."""
    await message.answer("Пожалуйста, используйте кнопки 'Да' или 'Нет' для ответа.")