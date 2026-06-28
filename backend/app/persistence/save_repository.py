from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.engine.core.world import World
from .database import Database
from .save_models import GameSave


class SaveRepository:
    def __init__(self, database: Database) -> None:
        self.database = database
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        self.database.execute(
            """
            CREATE TABLE IF NOT EXISTS world_saves (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                world_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                save_type TEXT NOT NULL,
                data TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _row_to_save(self, row: Any) -> GameSave:
        return GameSave(
            id=int(row["id"]),
            world_id=int(row["world_id"]),
            name=str(row["name"]),
            save_type=str(row["save_type"]),
            world_data_json=str(row["data"]),
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
        )

    def create_save(self, save: GameSave) -> GameSave:
        now = self._now()
        created_at = save.created_at or now
        updated_at = save.updated_at or now

        cursor = self.database.execute(
            """
            INSERT INTO world_saves (
                world_id, name, save_type, data, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                save.world_id,
                save.name,
                save.save_type,
                save.data_as_json_string(),
                created_at,
                updated_at,
            ),
        )
        return GameSave(
            id=int(cursor.lastrowid),
            world_id=save.world_id,
            name=save.name,
            save_type=save.save_type,
            world_data_json=save.world_data_json,
            created_at=created_at,
            updated_at=updated_at,
        )

    def update_save(self, save: GameSave) -> GameSave | None:
        if save.id is None:
            return None

        existing = self.get_save(save.id)
        if existing is None:
            return None

        updated_at = self._now()
        self.database.execute(
            """
            UPDATE world_saves
            SET world_id = ?, name = ?, save_type = ?, data = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                save.world_id,
                save.name,
                save.save_type,
                save.data_as_json_string(),
                updated_at,
                save.id,
            ),
        )
        return GameSave(
            id=save.id,
            world_id=save.world_id,
            name=save.name,
            save_type=save.save_type,
            world_data_json=save.world_data_json,
            created_at=existing.created_at,
            updated_at=updated_at,
        )

    def save(self, save: GameSave) -> GameSave:
        if save.id is None:
            return self.create_save(save)

        updated = self.update_save(save)
        if updated is None:
            return self.create_save(
                GameSave(
                    id=None,
                    world_id=save.world_id,
                    name=save.name,
                    save_type=save.save_type,
                    world_data_json=save.world_data_json,
                    created_at=save.created_at,
                    updated_at=save.updated_at,
                )
            )
        return updated

    def list_saves(self) -> list[GameSave]:
        rows = self.database.fetch_all(
            """
            SELECT id, world_id, name, save_type, data, created_at, updated_at
            FROM world_saves
            ORDER BY updated_at DESC, id DESC
            """
        )
        return [self._row_to_save(row) for row in rows]

    def get_save(self, save_id: int) -> GameSave | None:
        row = self.database.fetch_one(
            """
            SELECT id, world_id, name, save_type, data, created_at, updated_at
            FROM world_saves
            WHERE id = ?
            """,
            (save_id,),
        )
        if row is None:
            return None
        return self._row_to_save(row)

    def list_saves_by_world_id(self, world_id: int) -> list[GameSave]:
        rows = self.database.fetch_all(
            """
            SELECT id, world_id, name, save_type, data, created_at, updated_at
            FROM world_saves
            WHERE world_id = ?
            ORDER BY updated_at DESC, id DESC
            """,
            (world_id,),
        )
        return [self._row_to_save(row) for row in rows]

    def rename_save(self, save_id: int, new_name: str) -> bool:
        cursor = self.database.execute(
            """
            UPDATE world_saves
            SET name = ?, updated_at = ?
            WHERE id = ?
            """,
            (new_name, self._now(), save_id),
        )
        return cursor.rowcount > 0

    def delete_save(self, save_id: int) -> bool:
        cursor = self.database.execute(
            """
            DELETE FROM world_saves
            WHERE id = ?
            """,
            (save_id,),
        )
        return cursor.rowcount > 0

    def load_world(self, save_id: int) -> World | None:
        save = self.get_save(save_id)

        if save is None:
            return None

        return World.from_dict(save.data_as_dict())
    
