"""
Инициализация пакета handlers.
Экспортирует роутеры для подключения в главном файле.
"""

from .test_handlers import test_router
from .admin_handlers import admin_router

__all__ = ["test_router", "admin_router"]