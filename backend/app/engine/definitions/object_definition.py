from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ObjectDefinition:
    id: str
    name: str
    category: str
    stack_kind: str = "normal"
    entity_type: str | None = None
    stackable: bool = True
    max_stack: int = 999
    default_entity_data: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    icon: str = "object"
    visual_key: str = "object"
    model_key: str | None = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "stack_kind": self.stack_kind,
            "entity_type": self.entity_type,
            "stackable": self.stackable,
            "max_stack": self.max_stack,
            "default_entity_data": dict(self.default_entity_data),
            "metadata": dict(self.metadata),
            "icon": self.icon,
            "visual_key": self.visual_key,
            "model_key": self.model_key,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ObjectDefinition":
        return cls(
            id=data["id"],
            name=data["name"],
            category=data["category"],
            stack_kind=data.get("stack_kind", "normal"),
            entity_type=data.get("entity_type"),
            stackable=data.get("stackable", True),
            max_stack=int(data.get("max_stack", 999)),
            default_entity_data=dict(data.get("default_entity_data", {})),
            metadata=dict(data.get("metadata", {})),
            icon=data.get("icon", "object"),
            visual_key=data.get("visual_key", "object"),
            model_key=data.get("model_key"),
        )
