from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class GameSave:
    id: int | None
    world_id: int
    name: str
    save_type: str
    world_data_json: dict[str, Any] | str
    created_at: str | None = None
    updated_at: str | None = None

    def data_as_json_string(self) -> str:
        if isinstance(self.world_data_json, str):
            return self.world_data_json
        return json.dumps(self.world_data_json, ensure_ascii=False)

    def data_as_dict(self) -> dict[str, Any]:
        if isinstance(self.world_data_json, str):
            return json.loads(self.world_data_json)
        return dict(self.world_data_json)
