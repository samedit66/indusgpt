from dataclasses import dataclass, field
from functools import wraps
from pathlib import Path

import aiosqlite


@dataclass(slots=True)
class Database:
    """Simple human wrapper around aiosqlite.connect.

    Usage:

        db = Database("test.db")

        # Register schema or setup code (runs only once before first query)
        @db.before()
        async def init_db(db):
            await db.execute(\"""
                CREATE TABLE IF NOT EXISTS users (
                    id   INTEGER PRIMARY KEY,
                    name TEXT NOT NULL
                );
            \"""

        # Define your query functions
        @db.connect()
        async def insert_user(db, name: str):
            await db.execute(
                "INSERT INTO users (name) VALUES (?);",
                (name,)
            )

        @db.connect()
        async def get_users(db):
            cursor = await db.execute("SELECT * FROM users;")
            return await cursor.fetchall()
    """

    db_path: str | Path
    """Path to the SQLite database file (.db)."""

    _initialized: bool = field(init=False, default=False)
    """Indicates whether the registered before-hooks have been executed."""

    _before_hooks: list = field(init=False, default_factory=list)
    """A list of async callables to run before the first database operation."""

    def connect(self, row_factory=aiosqlite.Row):
        """
        Decorator that opens a database connection, sets the row factory,
        runs before-hooks once, then commits or rolls back around the decorated function.

        :param row_factory: Optional aiosqlite row factory (default: aiosqlite.Row)
        :returns: A decorator to wrap async DB functions.
        """

        def aux(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                async with aiosqlite.connect(self.db_path) as db:
                    db.row_factory = row_factory

                    if not self._initialized:
                        await self._perform_before_hooks(db)
                        self._initialized = True

                    try:
                        result = await func(db, *args, **kwargs)
                        await db.commit()
                        return result
                    except Exception:
                        await db.rollback()
                        raise

            return wrapper

        return aux

    async def _perform_before_hooks(self, db) -> None:
        for hook in self._before_hooks:
            await hook(db)

    def before(self):
        """
        Decorator to register an async function to run before the first DB operation.

        The decorated function should accept a single argument: the database connection.
        All before-hooks are run once, in registration order, before any queries.

        :returns: A decorator to register the before-hook.
        """

        def aux(func):
            self._before_hooks.append(func)
            return func

        return aux
