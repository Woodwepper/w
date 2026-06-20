from dataclasses import dataclass, field


@dataclass(frozen=True)
class ProducerDefinition:
    id: str
    name: str
    allowed_node_types: list[str] = field(default_factory=list)
    base_duration: float = 1.0
    base_output_amount: int = 1
    machine_id: str = ""
    icon: str = "producer"
    visual_key: str = "producer"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "allowed_node_types": list(self.allowed_node_types),
            "base_duration": self.base_duration,
            "base_output_amount": self.base_output_amount,
            "machine_id": self.machine_id,
            "icon": self.icon,
            "visual_key": self.visual_key,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ProducerDefinition":
        return cls(
            id=data["id"],
            name=data["name"],
            allowed_node_types=list(data.get("allowed_node_types", [])),
            base_duration=data.get("base_duration", 1.0),
            base_output_amount=data.get("base_output_amount", 1),
            machine_id=data.get("machine_id", ""),
            icon=data.get("icon", "producer"),
            visual_key=data.get("visual_key", "producer"),
        )
