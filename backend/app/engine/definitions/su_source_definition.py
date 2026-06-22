from dataclasses import dataclass, field


@dataclass(frozen=True)
class SUSourceDefinition:
    id: str
    name: str
    su_output: int
    build_cost: dict[str, int] = field(default_factory=dict)
    icon: str = "su_source"
    visual_key: str = "su_source"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "su_output": self.su_output,
            "build_cost": dict(self.build_cost),
            "icon": self.icon,
            "visual_key": self.visual_key,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SUSourceDefinition":
        return cls(
            id=data["id"],
            name=data["name"],
            su_output=int(data["su_output"]),
            build_cost=dict(data.get("build_cost", {})),
            icon=data.get("icon", "su_source"),
            visual_key=data.get("visual_key", "su_source"),
        )
