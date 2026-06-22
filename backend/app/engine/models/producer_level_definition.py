from dataclasses import dataclass, field


@dataclass(frozen=True)
class ProducerLevelDefinition:
    level: int
    machine_slots: int
    upgrade_cost: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "level": self.level,
            "machine_slots": self.machine_slots,
            "upgrade_cost": dict(self.upgrade_cost),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ProducerLevelDefinition":
        return cls(
            level=data["level"],
            machine_slots=data["machine_slots"],
            upgrade_cost=dict(data.get("upgrade_cost", {})),
        )
