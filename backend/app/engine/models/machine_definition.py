from dataclasses import dataclass, field


@dataclass(frozen=True)
class MachineDefinition:
    id: str
    name: str
    su_cost: int
    allowed_recipes: list[str] = field(default_factory=list)
    build_cost: dict[str, int] = field(default_factory=dict)
    upgrade_costs: dict[int, dict[str, int]] = field(default_factory=dict)
    speed_multipliers: dict[int, float] = field(default_factory=dict)
    icon: str = "machine"
    visual_key: str = "machine"

    def get_total_su(self, amount: int) -> int:
        return self.su_cost * amount

    def get_speed_multiplier(self, level: int) -> float:
        return self.speed_multipliers.get(level, 1.0)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "su_cost": self.su_cost,
            "allowed_recipes": list(self.allowed_recipes),
            "build_cost": dict(self.build_cost),
            "upgrade_costs": {
                level: dict(cost)
                for level, cost in self.upgrade_costs.items()
            },
            "speed_multipliers": dict(self.speed_multipliers),
            "icon": self.icon,
            "visual_key": self.visual_key,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MachineDefinition":
        return cls(
            id=data["id"],
            name=data["name"],
            su_cost=data["su_cost"],
            allowed_recipes=list(data.get("allowed_recipes", [])),
            build_cost=dict(data.get("build_cost", {})),
            upgrade_costs={
                int(level): dict(cost)
                for level, cost in data.get("upgrade_costs", {}).items()
            },
            speed_multipliers={
                int(level): float(multiplier)
                for level, multiplier in data.get("speed_multipliers", {}).items()
            },
            icon=data.get("icon", "machine"),
            visual_key=data.get("visual_key", "machine"),
        )


def __getattr__(name: str):
    if name == "MACHINE_DEFINITIONS":
        from app.engine.definitions.machine_definitions import MACHINE_DEFINITIONS

        return MACHINE_DEFINITIONS

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
