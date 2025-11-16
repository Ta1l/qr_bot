# your_bot/database/db_manager.py

"""
Модуль для управления базой данных SQLite.
Содержит функции для инициализации БД и сохранения/извлечения результатов тестов.
"""
import logging
import aiosqlite
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

DB_PATH = Path(__file__).parent.parent / "database.db"
logger = logging.getLogger(__name__)


async def init_db():
    """Инициализирует базу данных и создает таблицу, если она не существует."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS test_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT,
                name TEXT,                      -- НОВОЕ ПОЛЕ
                citizenship TEXT,
                card_arrests TEXT,              -- ПОЛЕ ПЕРЕИМЕНОВАНО
                phone_number TEXT,
                completion_date TEXT NOT NULL
            )
        ''')
        await db.commit()
    logger.info("База данных успешно инициализирована.")


async def save_test_result(state_data: dict):
    """Сохраняет данные из FSM состояния в базу данных."""
    params = (
        state_data.get("user_id"),
        state_data.get("username", "Без username"),
        state_data.get("name"),         # <-- Добавлено
        state_data.get("citizenship"),
        state_data.get("card_arrests"), # <-- Обновлено
        state_data.get("phone_number"),
        datetime.now().isoformat()
    )
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            '''INSERT INTO test_results 
               (user_id, username, name, citizenship, card_arrests, phone_number, completion_date) 
               VALUES (?, ?, ?, ?, ?, ?, ?)''', # <-- Обновлено
            params
        )
        await db.commit()
    logger.info(f"Результат для пользователя {state_data.get('user_id')} сохранен в БД.")


async def get_all_results() -> List[Dict[str, Any]]:
    """Возвращает список всех пользователей, прошедших тест."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT id, user_id, username FROM test_results ORDER BY id DESC") as cursor:
            return [dict(row) for row in await cursor.fetchall()]


async def get_result_by_id(record_id: int) -> Optional[Dict[str, Any]]:
    """Возвращает полную информацию о записи по её ID в базе."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM test_results WHERE id = ?", (record_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None