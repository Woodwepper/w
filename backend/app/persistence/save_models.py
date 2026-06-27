from datetime import datetime

class GameSave:
    def __init__(self, id: str, world_id: int, name: str, created_at: datetime, updated_at: datetime, world_data_json: dict):
        self.id = id
        self.world_id = world_id
        self.name = name
        self.created_at = created_at
        self.updated_at = updated_at
        self.world_data_json = world_data_json

