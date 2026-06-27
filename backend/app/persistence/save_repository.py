from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from app.engine.core.world import World

from .database import Database


@dataclass(frozen=True)
class SaveRecord:
    id: int
    world_id: int
    name: str
    save_type: str
    data: dict[str, Any]
    created_at: str
    updated_at: str


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
                updated_at TEXT NOT NULL,
                UNIQUE(world_id, save_type)
            )
            """
        )

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _row_to_record(self, row: Any) -> SaveRecord:
        return SaveRecord(
            id=int(row["id"]),
            world_id=int(row["world_id"]),
            name=str(row["name"]),
            save_type=str(row["save_type"]),
            data=json.loads(row["data"]),
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
        )

    def list_saves(self) -> list[dict[str, Any]]:
        rows = self.database.fetch_all(
            """
            SELECT id, world_id, name, save_type, created_at, updated_at
            FROM world_saves
            ORDER BY updated_at DESC, id DESC
            """
        )
        return [
            {
                "id": int(row["id"]),
                "world_id": int(row["world_id"]),
                "name": str(row["name"]),
                "save_type": str(row["save_type"]),
                "created_at": str(row["created_at"]),
                "updated_at": str(row["updated_at"]),
            }
            for row in rows
        ]

    def get_save(self, world_id: int, save_type: str = "manual") -> dict[str, Any] | None:
        row = self.database.fetch_one(
            """
            SELECT id, world_id, name, save_type, data, created_at, updated_at
            FROM world_saves
            WHERE world_id = ? AND save_type = ?
            """,
            (world_id, save_type),
        )
        if row is None:
            return None
        record = self._row_to_record(row)
        return {
            "id": record.id,
            "world_id": record.world_id,
            "name": record.name,
            "save_type": record.save_type,
            "data": record.data,
            "created_at": record.created_at,
            "updated_at": record.updated_at,
        }

    def load_save(self, world_id: int, save_type: str = "manual") -> World | None:
        save = self.get_save(world_id, save_type)
        if save is None:
            return None
        return World.from_dict(save["data"])

    def save_world(
        self,
        world: World,
        name: str | None = None,
        save_type: str = "manual",
    ) -> dict[str, Any]:
        payload = json.dumps(world.to_dict(), ensure_ascii=False)
        now = self._now()
        save_name = name or world.name

        existing = self.get_save(world.id, save_type)
        if existing is None:
            cursor = self.database.execute(
                """
                INSERT INTO world_saves (
                    world_id, name, save_type, data, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (world.id, save_name, save_type, payload, now, now),
            )
            save_id = int(cursor.lastrowid)
            return {
                "id": save_id,
                "world_id": world.id,
                "name": save_name,
                "save_type": save_type,
                "data": world.to_dict(),
                "created_at": now,
                "updated_at": now,
            }

        self.database.execute(
            """
            UPDATE world_saves
            SET name = ?, data = ?, updated_at = ?
            WHERE world_id = ? AND save_type = ?
            """,
            (save_name, payload, now, world.id, save_type),
        )
        return {
            "id": existing["id"],
            "world_id": world.id,
            "name": save_name,
            "save_type": save_type,
            "data": world.to_dict(),
            "created_at": existing["created_at"],
            "updated_at": now,
        }

    def rename_save(
        self,
        world_id: int,
        new_name: str,
        save_type: str = "manual",
    ) -> bool:
        cursor = self.database.execute(
            """
            UPDATE world_saves
            SET name = ?, updated_at = ?
            WHERE world_id = ? AND save_type = ?
            """,
            (new_name, self._now(), world_id, save_type),
        )
        return cursor.rowcount > 0

    def delete_save(self, world_id: int, save_type: str = "manual") -> bool:
        cursor = self.database.execute(
            """
            DELETE FROM world_saves
            WHERE world_id = ? AND save_type = ?
            """,
            (world_id, save_type),
        )
        return cursor.rowcount > 0

    def autosave(self, world: World) -> dict[str, Any]:
        return self.save_world(world, name=f"{world.name} Autosave", save_type="autosave")

    def quicksave(self, world: World) -> dict[str, Any]:
        return self.save_world(world, name=f"{world.name} Quicksave", save_type="quicksave")

    def list_world_ids(self) -> list[int]:
        rows = self.database.fetch_all(
            """
            SELECT DISTINCT world_id
            FROM world_saves
            ORDER BY world_id ASC
            """
        )
        return [int(row["world_id"]) for row in rows]

    def save_exists(self, world_id: int, save_type: str = "manual") -> bool:
        return self.get_save(world_id, save_type) is not None

    def load_or_create_world_save(self, world: World, save_type: str = "manual") -> dict[str, Any]:
        return self.save_world(world, save_type=save_type)
