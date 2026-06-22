from dataclasses import dataclass, field


@dataclass(frozen=True)
class FactoryLevelDefinition:
    level: int
    module_slots: int
    machine_slots_per_module: int
    upgrade_cost: dict[str, int] = field(default_factory=dict)
