from dataclasses import dataclass, field

from app.engine.definitions.su_producer_level_definition import (
    SUProducerLevelDefinition,
)


@dataclass(frozen=True)
class SUProducerDefinition:
    id: str
    name: str
    allowed_unit_types: list[str] = field(default_factory=list)
    levels: dict[int, SUProducerLevelDefinition] = field(default_factory=dict)
    icon: str = "su_producer"
    visual_key: str = "su_producer"

    def get_level_definition(
        self,
        level: int,
    ) -> SUProducerLevelDefinition | None:
        return self.levels.get(level)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "allowed_unit_types": list(self.allowed_unit_types),
            "levels": {
                level: level_definition.to_dict()
                for level, level_definition in self.levels.items()
            },
            "icon": self.icon,
            "visual_key": self.visual_key,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SUProducerDefinition":
        return cls(
            id=data["id"],
            name=data["name"],
            allowed_unit_types=list(data.get("allowed_unit_types", [])),
            levels={
                int(level): SUProducerLevelDefinition.from_dict(level_definition)
                for level, level_definition in data.get("levels", {}).items()
            },
            icon=data.get("icon", "su_producer"),
            visual_key=data.get("visual_key", "su_producer"),
        )
