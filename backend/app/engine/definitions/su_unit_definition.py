from dataclasses import dataclass, field


@dataclass(frozen=True)
class SUUnitDefinition:
    id: str
    name: str
    su_output: int
    input_items: dict[str, int] = field(default_factory=dict)
    build_cost: dict[str, int] = field(default_factory=dict)
    icon: str = "su_unit"
    visual_key: str = "su_unit"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "su_output": self.su_output,
            "input_items": dict(self.input_items),
            "build_cost": dict(self.build_cost),
            "icon": self.icon,
            "visual_key": self.visual_key,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SUUnitDefinition":
        return cls(
            id=data["id"],
            name=data["name"],
            su_output=int(data["su_output"]),
            input_items=dict(data.get("input_items", {})),
            build_cost=dict(data.get("build_cost", {})),
            icon=data.get("icon", "su_unit"),
            visual_key=data.get("visual_key", "su_unit"),
        )
