from dataclasses import dataclass, field


@dataclass(frozen=True)
class ResourceNodeDefinition:
    id: str
    name: str
    resource_type: str
    can_be_infinite: bool = False
    default_richness: int = 1
    default_hardness: float = 1.0
    default_required_machine_level: int = 1
    min_stock: int | None = None
    max_stock: int | None = None
    traits: list[str] = field(default_factory=list)
    icon: str = "resource_node"
    visual_key: str = "resource_node"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "resource_type": self.resource_type,
            "can_be_infinite": self.can_be_infinite,
            "default_richness": self.default_richness,
            "default_hardness": self.default_hardness,
            "default_required_machine_level": self.default_required_machine_level,
            "min_stock": self.min_stock,
            "max_stock": self.max_stock,
            "traits": list(self.traits),
            "icon": self.icon,
            "visual_key": self.visual_key,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ResourceNodeDefinition":
        return cls(
            id=data["id"],
            name=data["name"],
            resource_type=data["resource_type"],
            can_be_infinite=data.get("can_be_infinite", False),
            default_richness=data.get("default_richness", 1),
            default_hardness=data.get("default_hardness", 1.0),
            default_required_machine_level=data.get(
                "default_required_machine_level",
                1,
            ),
            min_stock=data.get("min_stock"),
            max_stock=data.get("max_stock"),
            traits=list(data.get("traits", [])),
            icon=data.get("icon", "resource_node"),
            visual_key=data.get("visual_key", "resource_node"),
        )
