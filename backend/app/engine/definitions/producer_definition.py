from dataclasses import dataclass, field

from .producer_level_definition import ProducerLevelDefinition


@dataclass(frozen=True)
class ProducerDefinition:
    id: str
    name: str
    allowed_node_types: list[str] = field(default_factory=list)
    allowed_machine_types: list[str] = field(default_factory=list)
    base_duration: float = 1.0
    base_output_amount: int = 1
    levels: dict[int, ProducerLevelDefinition] = field(default_factory=dict)
    icon: str = "producer"
    visual_key: str = "producer"

    def get_level_definition(self, level: int) -> ProducerLevelDefinition | None:
        return self.levels.get(level)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "allowed_node_types": list(self.allowed_node_types),
            "allowed_machine_types": list(self.allowed_machine_types),
            "base_duration": self.base_duration,
            "base_output_amount": self.base_output_amount,
            "levels": {
                level: level_definition.to_dict()
                for level, level_definition in self.levels.items()
            },
            "icon": self.icon,
            "visual_key": self.visual_key,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ProducerDefinition":
        return cls(
            id=data["id"],
            name=data["name"],
            allowed_node_types=list(data.get("allowed_node_types", [])),
            allowed_machine_types=list(data.get("allowed_machine_types", [])),
            base_duration=data.get("base_duration", 1.0),
            base_output_amount=data.get("base_output_amount", 1),
            levels={
                int(level): ProducerLevelDefinition.from_dict(level_definition)
                for level, level_definition in data.get("levels", {}).items()
            },
            icon=data.get("icon", "producer"),
            visual_key=data.get("visual_key", "producer"),
        )
