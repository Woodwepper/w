from dataclasses import dataclass, field


@dataclass(frozen=True)
class FactoryLevelDefinition:
    level: int
    module_slots: int
    machine_slots_per_module: int
    upgrade_cost: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "level": self.level,
            "module_slots": self.module_slots,
            "machine_slots_per_module": self.machine_slots_per_module,
            "upgrade_cost": dict(self.upgrade_cost),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "FactoryLevelDefinition":
        return cls(
            level=int(data["level"]),
            module_slots=int(data["module_slots"]),
            machine_slots_per_module=int(data["machine_slots_per_module"]),
            upgrade_cost=dict(data.get("upgrade_cost", {})),
        )
