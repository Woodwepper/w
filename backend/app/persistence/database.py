from __future__ import annotations

import logging
import sqlite3
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, db_file: str | Path) -> None:
        self.db_file = str(db_file)
        self.connection: sqlite3.Connection | None = None
        self.connect()

    def connect(self) -> sqlite3.Connection:
        if self.connection is not None:
            return self.connection

        try:
            self.connection = sqlite3.connect(self.db_file)
            self.connection.row_factory = sqlite3.Row
            logger.info("Database connection established: %s", self.db_file)
            return self.connection
        except sqlite3.Error as exc:
            logger.exception("Error connecting to database: %s", exc)
            raise

    def close(self) -> None:
        if self.connection is None:
            return

        self.connection.close()
        self.connection = None
        logger.info("Database connection closed.")

    def execute(
        self,
        query: str,
        params: tuple[Any, ...] | list[Any] | dict[str, Any] | None = None,
    ) -> sqlite3.Cursor:
        connection = self.connect()
        cursor = connection.cursor()

        try:
            if params is None:
                cursor.execute(query)
            else:
                cursor.execute(query, params)
            connection.commit()
            return cursor
        except sqlite3.Error as exc:
            connection.rollback()
            logger.exception("Error executing query: %s", exc)
            raise

    def fetch_one(
        self,
        query: str,
        params: tuple[Any, ...] | list[Any] | dict[str, Any] | None = None,
    ) -> sqlite3.Row | None:
        cursor = self.execute(query, params)
        return cursor.fetchone()

    def fetch_all(
        self,
        query: str,
        params: tuple[Any, ...] | list[Any] | dict[str, Any] | None = None,
    ) -> list[sqlite3.Row]:
        cursor = self.execute(query, params)
        return cursor.fetchall()

    def execute_query(
        self,
        query: str,
        params: tuple[Any, ...] | list[Any] | dict[str, Any] | None = None,
    ) -> list[sqlite3.Row]:
        return self.fetch_all(query, params)
