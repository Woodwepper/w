from dataclasses import dataclass, field


@dataclass(frozen=True)
class ModuleDefinition:
    id: str
    name: str
    allowed_recipes: list[str] = field(default_factory=list)
    allowed_machine_types: list[str] = field(default_factory=list)
    icon: str = "module"
    visual_key: str = "default"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "allowed_recipes": list(self.allowed_recipes),
            "allowed_machine_types": list(self.allowed_machine_types),
            "icon": self.icon,
            "visual_key": self.visual_key,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ModuleDefinition":
        return cls(
            id=data["id"],
            name=data["name"],
            allowed_recipes=list(data.get("allowed_recipes", [])),
            allowed_machine_types=list(data.get("allowed_machine_types", [])),
            icon=data.get("icon", "module"),
            visual_key=data.get("visual_key", "default"),
        )
