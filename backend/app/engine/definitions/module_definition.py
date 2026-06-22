from dataclasses import dataclass, field

from app.engine.entities.module_instance import ModuleInstance


@dataclass(frozen=True, init=False)
class ModuleDefinition:
    id: str
    name: str
    allowed_recipes: list[str] = field(default_factory=list)
    allowed_machine_types: list[str] = field(default_factory=list)
    icon: str = "module"
    visual_key: str = "default"

    def __init__(
        self,
        id: str,
        name: str,
        allowed_recipes: list[str] | None = None,
        allowed_machine_types: list[str] | None = None,
        icon: str = "module",
        visual_key: str = "default",
        machines: dict[str, int] | None = None,
    ) -> None:
        if allowed_machine_types is None and machines is not None:
            allowed_machine_types = list(machines)

        object.__setattr__(self, "id", id)
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "allowed_recipes", list(allowed_recipes or []))
        object.__setattr__(
            self,
            "allowed_machine_types",
            list(allowed_machine_types or []),
        )
        object.__setattr__(self, "icon", icon)
        object.__setattr__(self, "visual_key", visual_key)


def get_module_definition(module_type: str) -> ModuleDefinition | None:
    from app.engine.content.module_definitions import MODULE_DEFINITIONS

    return MODULE_DEFINITIONS.get(module_type)


def module_exists(module_type: str) -> bool:
    return get_module_definition(module_type) is not None


def module_allows_recipe(module_type: str, recipe_id: str) -> bool:
    module_definition = get_module_definition(module_type)
    if module_definition is None:
        return False
    return recipe_id in module_definition.allowed_recipes


def module_allows_machine_type(module_type: str, machine_type: str) -> bool:
    module_definition = get_module_definition(module_type)
    if module_definition is None:
        return False
    return machine_type in module_definition.allowed_machine_types


def get_module_effective_machines(module: ModuleInstance) -> dict[str, int]:
    machines: dict[str, int] = {}
    for machine in module.installed_machines:
        machines[machine.machine_type] = machines.get(machine.machine_type, 0) + 1
    return machines


def get_machine_count_for_level(level: int) -> int:
    return max(1, level)


def get_efficiency_multiplier_for_level(level: int) -> float:
    return 1.0


def __getattr__(name: str):
    if name == "MODULE_DEFINITIONS":
        from app.engine.content import module_definitions

        return module_definitions.MODULE_DEFINITIONS

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
