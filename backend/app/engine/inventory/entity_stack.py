from dataclasses import dataclass, field
from typing import Any


@dataclass
class EntityStack:
    object_id: str
    entity_type: str
    amount: int = 1
    entity_data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "object_id": self.object_id,
            "entity_type": self.entity_type,
            "amount": self.amount,
            "entity_data": dict(self.entity_data),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "EntityStack":
        return cls(
            object_id=data["object_id"],
            entity_type=data["entity_type"],
            amount=int(data.get("amount", 1)),
            entity_data=dict(data.get("entity_data", {})),
        )
