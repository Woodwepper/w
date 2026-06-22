from dataclasses import dataclass, field


@dataclass(frozen=True)
class SUSourceDefinition:
    id: str
    name: str
    su_output: int
    build_cost: dict[str, int] = field(default_factory=dict)
    icon: str = "su_source"
    visual_key: str = "su_source"
