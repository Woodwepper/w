from dataclasses import dataclass, field


@dataclass(frozen=True)
class SUProducerLevelDefinition:
    level: int
    unit_slots: int
    upgrade_cost: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "level": self.level,
            "unit_slots": self.unit_slots,
            "upgrade_cost": dict(self.upgrade_cost),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SUProducerLevelDefinition":
        return cls(
            level=int(data["level"]),
            unit_slots=int(data["unit_slots"]),
            upgrade_cost=dict(data.get("upgrade_cost", {})),
        )
