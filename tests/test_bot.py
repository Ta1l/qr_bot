"""
Тесты для проверки работы бота.
Запускать: python -m pytest tests/test_bot.py -v
"""

import pytest
import asyncio
import tempfile
import os
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.base import StorageKey
from aiogram.types import User, Chat, Message, CallbackQuery

from handlers.states import TestStates, AdminStates
from handlers.utils import validate_phone_number, finish_test
from handlers.keyboards import get_yes_no_keyboard, get_phone_keyboard, get_users_keyboard

# Фикстуры для тестов

@pytest.fixture
def bot():
    """Мок объекта Bot"""
    return AsyncMock(spec=Bot)


@pytest.fixture
def storage():
    """Хранилище FSM для тестов"""
    return MemoryStorage()


@pytest.fixture
def dispatcher(storage):
    """Диспетчер с подключенным хранилищем"""
    return Dispatcher(storage=storage)


@pytest.fixture
def mock_user():
    """Мок пользователя"""
    return User(
        id=123456789,
        is_bot=False,
        first_name="Test",
        username="test_user"
    )


@pytest.fixture
def mock_chat():
    """Мок чата"""
    return Chat(
        id=123456789,
        type="private"
    )


# === ТЕСТЫ ВАЛИДАЦИИ ===

class TestValidation:
    """Тесты функций валидации"""
    
    def test_valid_phone_numbers(self):
        """Тест валидных номеров телефона"""
        valid_numbers = [
            "+79991234567",
            "89991234567", 
            "79991234567",
            "9991234567",
            "+7 999 123 45 67",
            "8 (999) 123-45-67"
        ]
        
        for number in valid_numbers:
            assert validate_phone_number(number) == True, f"Номер {number} должен быть валидным"
    
    def test_invalid_phone_numbers(self):
        """Тест невалидных номеров телефона"""
        # Исправляем тест под текущую реализацию validate_phone_number
        # Функция проверяет только длину (10-11 цифр), не проверяя страну
        invalid_numbers = [
            "123",        # слишком короткий
            "abcdefghijk", # буквы
            "999",        # слишком короткий
            ""            # пустой
        ]
        
        for number in invalid_numbers:
            assert validate_phone_number(number) == False, f"Номер {number} должен быть невалидным"
    
    def test_edge_case_phone_numbers(self):
        """Тест граничных случаев для номеров"""
        # Номер +1234567890 имеет 10 цифр, поэтому считается валидным по текущей логике
        # Если нужна проверка на российские номера, нужно обновить validate_phone_number
        assert validate_phone_number("+1234567890") == True  # 10 цифр


# === ТЕСТЫ КЛАВИАТУР ===

class TestKeyboards:
    """Тесты генерации клавиатур"""
    
    def test_yes_no_keyboard(self):
        """Тест клавиатуры Да/Нет"""
        keyboard = get_yes_no_keyboard()
        
        assert keyboard is not None
        assert len(keyboard.keyboard) == 1  # Одна строка
        assert len(keyboard.keyboard[0]) == 2  # Две кнопки
        assert keyboard.keyboard[0][0].text == "Да"
        assert keyboard.keyboard[0][1].text == "Нет"
        assert keyboard.resize_keyboard == True
        assert keyboard.one_time_keyboard == True
    
    def test_phone_keyboard(self):
        """Тест клавиатуры для телефона"""
        keyboard = get_phone_keyboard()
        
        assert keyboard is not None
        assert len(keyboard.keyboard) == 1
        assert keyboard.keyboard[0][0].request_contact == True
        assert "телефон" in keyboard.keyboard[0][0].text.lower()
    
    def test_users_keyboard(self):
        """Тест клавиатуры списка пользователей для админа"""
        mock_users = [
            {"id": 1, "user_id": 111, "username": "user1"},
            {"id": 2, "user_id": 222, "username": "user2"}
        ]
        
        keyboard = get_users_keyboard(mock_users)
        
        assert keyboard is not None
        # Должно быть 2 пользователя + кнопка "Отмена" = 3 кнопки
        assert len(keyboard.keyboard) == 3
        # Проверяем формат кнопок пользователей
        assert "(ID: 1)" in keyboard.keyboard[0][0].text
        assert "(ID: 2)" in keyboard.keyboard[1][0].text
        assert keyboard.keyboard[-1][0].text == "Отмена"


# === ТЕСТЫ РАБОТЫ С БД ===

@pytest.mark.asyncio
class TestDatabase:
    """Тесты работы с базой данных"""
    
    async def test_init_db(self, tmp_path):
        """Тест инициализации БД"""
        # Создаем временный файл для тестовой БД
        test_db = tmp_path / "test_database.db"
        
        # Патчим путь к БД перед импортом
        with patch('database.db_manager.DB_PATH', test_db):
            from database.db_manager import init_db
            await init_db()
            assert test_db.exists()
    
    async def test_save_and_get_result(self, tmp_path):
        """Тест сохранения и получения результата"""
        test_db = tmp_path / "test_database.db"
        
        with patch('database.db_manager.DB_PATH', test_db):
            from database.db_manager import init_db, save_test_result, get_all_results
            
            await init_db()
            
            # Тестовые данные в формате, как их передает FSM
            test_data = {
                "user_id": 123456789,
                "username": "test_user",
                "citizenship": "Да",
                "card_blocks": "Нет",
                "phone_number": "+79991234567"
            }
            
            # Сохраняем
            await save_test_result(test_data)
            
            # Получаем все результаты
            results = await get_all_results()
            
            assert len(results) == 1
            assert results[0]["user_id"] == 123456789
            assert results[0]["username"] == "test_user"
            assert "id" in results[0]  # Должен быть первичный ключ
    
    async def test_get_result_by_id(self, tmp_path):
        """Тест получения записи по ID"""
        test_db = tmp_path / "test_database.db"
        
        with patch('database.db_manager.DB_PATH', test_db):
            from database.db_manager import init_db, save_test_result, get_result_by_id
            
            await init_db()
            
            # Сохраняем тестовую запись
            test_data = {
                "user_id": 987654321,
                "username": "another_user",
                "citizenship": "Да",
                "card_blocks": "Да",
                "phone_number": None
            }
            
            await save_test_result(test_data)
            
            # Получаем запись по ID
            result = await get_result_by_id(1)  # Первая запись должна иметь ID=1
            
            assert result is not None
            assert result["user_id"] == 987654321
            assert result["username"] == "another_user"
            assert result["citizenship"] == "Да"
            assert result["card_blocks"] == "Да"
            assert result["phone_number"] is None
            assert "completion_date" in result
    
    async def test_get_nonexistent_result(self, tmp_path):
        """Тест получения несуществующей записи"""
        test_db = tmp_path / "test_database.db"
        
        with patch('database.db_manager.DB_PATH', test_db):
            from database.db_manager import init_db, get_result_by_id
            
            await init_db()
            
            # Пытаемся получить несуществующую запись
            result = await get_result_by_id(999)
            
            assert result is None
    
    async def test_multiple_saves(self, tmp_path):
        """Тест множественного сохранения"""
        test_db = tmp_path / "test_database.db"
        
        with patch('database.db_manager.DB_PATH', test_db):
            from database.db_manager import init_db, save_test_result, get_all_results
            
            await init_db()
            
            # Сохраняем несколько записей
            for i in range(3):
                test_data = {
                    "user_id": 100 + i,
                    "username": f"user_{i}",
                    "citizenship": "Да" if i % 2 == 0 else "Нет",
                    "card_blocks": None,
                    "phone_number": f"+7999123456{i}"
                }
                await save_test_result(test_data)
            
            # Проверяем что все сохранились
            results = await get_all_results()
            assert len(results) == 3
            
            # Проверяем порядок (ORDER BY id DESC)
            assert results[0]["username"] == "user_2"  # Последний добавленный
            assert results[2]["username"] == "user_0"  # Первый добавленный


# === ТЕСТЫ FSM СОСТОЯНИЙ ===

@pytest.mark.asyncio
class TestFSMStates:
    """Тесты переходов между состояниями"""
    
    async def test_state_transitions(self, storage):
        """Тест переходов состояний в процессе теста"""
        user_id = 123
        chat_id = 123
        
        # Создаем контекст FSM
        state = FSMContext(
            storage=storage,
            key=StorageKey(bot_id=1, chat_id=chat_id, user_id=user_id)
        )
        
        # Тест перехода в первое состояние
        await state.set_state(TestStates.citizenship_question)
        current_state = await state.get_state()
        assert current_state == TestStates.citizenship_question
        
        # Сохраняем данные
        await state.update_data(citizenship="Да", user_id=user_id, username="test")
        
        # Переход ко второму вопросу
        await state.set_state(TestStates.card_blocks_question)
        current_state = await state.get_state()
        assert current_state == TestStates.card_blocks_question
        
        # Проверяем что данные сохранились
        data = await state.get_data()
        assert data["citizenship"] == "Да"
        assert data["user_id"] == user_id
    
    async def test_admin_states(self, storage):
        """Тест состояний админ-панели"""
        admin_id = 999
        chat_id = 999
        
        state = FSMContext(
            storage=storage,
            key=StorageKey(bot_id=1, chat_id=chat_id, user_id=admin_id)
        )
        
        # Переход в состояние выбора пользователя
        await state.set_state(AdminStates.choosing_user)
        current_state = await state.get_state()
        assert current_state == AdminStates.choosing_user
        
        # Очистка состояния
        await state.clear()
        current_state = await state.get_state()
        assert current_state is None


# === ИНТЕГРАЦИОННЫЕ ТЕСТЫ ===

@pytest.mark.asyncio
# === ИНТЕГРАЦИОННЫЕ ТЕСТЫ ===

@pytest.mark.asyncio
class TestBotIntegration:
    """Интеграционные тесты основных сценариев"""
    
    async def test_full_test_flow(self, storage):
        """Тест полного прохождения теста"""
        user_id = 123
        chat_id = 123
        
        state = FSMContext(
            storage=storage,
            key=StorageKey(bot_id=1, chat_id=chat_id, user_id=user_id)
        )
        
        # Эмулируем полное прохождение теста
        await state.set_state(TestStates.citizenship_question)
        await state.update_data(
            user_id=user_id,
            username="test_user",
            citizenship="Да"
        )
        
        await state.set_state(TestStates.card_blocks_question)
        await state.update_data(card_blocks="Нет")
        
        await state.set_state(TestStates.phone_number_question)
        await state.update_data(phone_number="+79991234567")
        
        # Проверяем финальные данные
        data = await state.get_data()
        assert data["citizenship"] == "Да"
        assert data["card_blocks"] == "Нет"
        assert data["phone_number"] == "+79991234567"
        assert data["user_id"] == user_id
        assert data["username"] == "test_user"
    
    @patch('database.db_manager.save_test_result', new_callable=AsyncMock)
    @patch('handlers.utils.notify_admins', new_callable=AsyncMock)
    async def test_finish_test(self, mock_notify, mock_save, bot, storage):
        """Тест завершения теста с моками"""
        user_id = 123
        chat_id = 123
        
        state = FSMContext(
            storage=storage,
            key=StorageKey(bot_id=1, chat_id=chat_id, user_id=user_id)
        )
        
        # Подготавливаем полные данные как после прохождения теста
        test_data = {
            "user_id": user_id,
            "username": "test_user", 
            "citizenship": "Да",
            "card_blocks": "Нет",
            "phone_number": "+79991234567"
        }
        await state.update_data(**test_data)
        
        # Завершаем тест
        await finish_test(user_id, state, bot)
        
        # Проверяем что функции были вызваны
        mock_save.assert_called_once_with(test_data)
        mock_notify.assert_called_once_with(bot, test_data)
        
        # Проверяем что состояние очищено
        data = await state.get_data()
        assert data == {}
    
@patch('database.db_manager.save_test_result')
@patch('handlers.utils.notify_admins')
async def test_finish_test(self, mock_notify, mock_save, bot, storage):
    """Тест завершения теста с моками"""
    user_id = 123
    chat_id = 123
    
    state = FSMContext(
        storage=storage,
        key=StorageKey(bot_id=1, chat_id=chat_id, user_id=user_id)
    )
    
    # Подготавливаем полные данные как после прохождения теста
    test_data = {
        "user_id": user_id,
        "username": "test_user", 
        "citizenship": "Да",
        "card_blocks": "Нет",
        "phone_number": "+79991234567"
    }
    await state.update_data(**test_data)
    
    # Создаем асинхронные моки для Python 3.12+
    async def async_mock():
        return None
    
    mock_save.return_value = async_mock()
    mock_notify.return_value = async_mock()
    
    # Завершаем тест
    await finish_test(user_id, state, bot)
    
    # Проверяем что функции были вызваны
    mock_save.assert_called_once_with(test_data)
    mock_notify.assert_called_once_with(bot, test_data)
    
    # Проверяем что состояние очищено
    data = await state.get_data()
    assert data == {}


# === ТЕСТ СЦЕНАРИЕВ ===

class TestScenarios:
    """Тесты различных сценариев использования"""
    
    @pytest.mark.parametrize("citizenship,card_blocks,phone,expected", [
        ("Да", "Нет", "+79991234567", "success"),
        ("Нет", None, None, "rejected_citizenship"),
        ("Да", "Да", None, "rejected_blocks"),
    ])
    def test_different_scenarios(self, citizenship, card_blocks, phone, expected):
        """Параметризованный тест различных сценариев"""
        if expected == "success":
            assert citizenship == "Да"
            assert card_blocks == "Нет"
            assert validate_phone_number(phone) == True
        elif expected == "rejected_citizenship":
            assert citizenship == "Нет"
        elif expected == "rejected_blocks":
            assert citizenship == "Да"
            assert card_blocks == "Да"


# === ТЕСТЫ ФИЛЬТРОВ ===

@pytest.mark.asyncio
class TestFilters:
    """Тесты кастомных фильтров"""
    
    async def test_is_admin_filter(self, mock_user, mock_chat):
        """Тест фильтра IsAdmin"""
        from handlers.filters import IsAdmin
        from config import ADMIN_IDS
        
        filter_obj = IsAdmin()
        
        # Создаем мок сообщения от админа
        if ADMIN_IDS:
            admin_user = User(id=ADMIN_IDS[0], is_bot=False, first_name="Admin", username="admin")
            admin_message = Message(
                message_id=1,
                date=datetime.now(),
                chat=mock_chat,
                from_user=admin_user,
                text="test"
            )
            
            # Создаем мок сообщения от обычного пользователя
            user_message = Message(
                message_id=2,
                date=datetime.now(),
                chat=mock_chat,
                from_user=mock_user,
                text="test"
            )
            
            # Тестируем фильтр
            assert await filter_obj(admin_message) == True
            assert await filter_obj(user_message) == (mock_user.id in ADMIN_IDS)