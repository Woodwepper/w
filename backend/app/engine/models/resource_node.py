from dataclasses import dataclass, field


@dataclass
class ResourceNode:
    id: int
    node_type: str
    name: str
    x: int
    y: int
    richness: int = 1
    hardness: float = 1.0
    required_machine_level: int = 1
    remaining_amount: int | None = None
    infinite: bool = False
    traits: list[str] = field(default_factory=list)

    def is_depleted(self) -> bool:
        return (
            not self.infinite
            and self.remaining_amount is not None
            and self.remaining_amount <= 0
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "node_type": self.node_type,
            "name": self.name,
            "x": self.x,
            "y": self.y,
            "richness": self.richness,
            "hardness": self.hardness,
            "required_machine_level": self.required_machine_level,
            "remaining_amount": self.remaining_amount,
            "infinite": self.infinite,
            "traits": list(self.traits),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ResourceNode":
        return cls(
            id=data["id"],
            node_type=data["node_type"],
            name=data["name"],
            x=data["x"],
            y=data["y"],
            richness=data.get("richness", 1),
            hardness=data.get("hardness", 1.0),
            required_machine_level=data.get("required_machine_level", 1),
            remaining_amount=data.get("remaining_amount"),
            infinite=data.get("infinite", False),
            traits=list(data.get("traits", [])),
        )
