"""Database package for Safe Wealth Advisory system.
Provides SQLite persistence, schema management, and relational CRUD operations.
"""
from .schema import init_db, get_connection
from .repository import WealthRepository

__all__ = ["init_db", "get_connection", "WealthRepository"]
