from typing import Any

from app.engine.instances.machine_instance import MachineInstance
from app.engine.instances.module_instance import ModuleInstance
from app.engine.models.factory_building import FactoryBuilding
from app.engine.models.game_definitions import GameDefinitions
from app.engine.models.world import World


def _has_resources(inventory: dict[str, int], cost: dict[str, int]) -> bool:
    for item_id, amount in cost.items():
        if inventory.get(item_id, 0) < amount:
            return False
    return True


def _consume_resources(inventory: dict[str, int], cost: dict[str, int]) -> None:
    for item_id, amount in cost.items():
        remaining_amount = inventory.get(item_id, 0) - amount
        if remaining_amount <= 0:
            inventory.pop(item_id, None)
        else:
            inventory[item_id] = remaining_amount


def can_build_machine_from_resources(
    inventory: dict[str, int],
    definitions: GameDefinitions,
    machine_type: str,
) -> bool:
    machine_definition = definitions.get_machine(machine_type)
    if machine_definition is None:
        return False

    return _has_resources(inventory, machine_definition.build_cost)


def build_machine_from_resources(
    inventory: dict[str, int],
    definitions: GameDefinitions,
    machine_type: str,
    machine_id: int,
    level: int = 1,
    metadata: dict[str, Any] | None = None,
) -> MachineInstance | None:
    machine_definition = definitions.get_machine(machine_type)
    if machine_definition is None:
        return None

    if not _has_resources(inventory, machine_definition.build_cost):
        return None

    _consume_resources(inventory, machine_definition.build_cost)

    return MachineInstance(
        id=machine_id,
        machine_type=machine_type,
        level=max(1, level),
        metadata=dict(metadata or {}),
    )


def can_install_machine_in_module(
    factory: FactoryBuilding | None,
    module: ModuleInstance | None,
    machine: MachineInstance | None,
    definitions: GameDefinitions,
) -> bool:
    if factory is None or module is None or machine is None:
        return False

    if module not in factory.modules:
        return False

    module_definition = definitions.get_module(module.module_type)
    if module_definition is None:
        return False

    machine_definition = definitions.get_machine(machine.machine_type)
    if machine_definition is None:
        return False

    if machine.machine_type not in module_definition.allowed_machine_types:
        return False

    if module.get_machine(machine.id) is not None:
        return False

    if len(module.installed_machines) >= factory.get_machine_slot_limit_per_module(definitions):
        return False

    return True


def install_machine_in_module(
    factory: FactoryBuilding | None,
    module_id: int,
    machine: MachineInstance,
    definitions: GameDefinitions,
) -> bool:
    if factory is None:
        return False

    module = factory.get_module(module_id)
    if not can_install_machine_in_module(factory, module, machine, definitions):
        return False

    module.add_machine(machine)
    return True


def build_and_install_machine_from_resources(
    world: World | None,
    factory_id: int,
    module_id: int,
    machine_type: str,
    machine_id: int,
    level: int = 1,
    metadata: dict[str, Any] | None = None,
) -> bool:
    if world is None:
        return False

    factory = world.get_factory(factory_id)
    if factory is None:
        return False

    module = factory.get_module(module_id)
    if module is None:
        return False

    proposed_machine = MachineInstance(
        id=machine_id,
        machine_type=machine_type,
        level=max(1, level),
        metadata=dict(metadata or {}),
    )

    if not can_install_machine_in_module(
        factory,
        module,
        proposed_machine,
        world.definitions,
    ):
        return False

    machine = build_machine_from_resources(
        world.inventory,
        world.definitions,
        machine_type,
        machine_id,
        level=level,
        metadata=metadata,
    )
    if machine is None:
        return False

    module.add_machine(machine)
    return True


def can_upgrade_machine(
    inventory: dict[str, int],
    definitions: GameDefinitions,
    machine: MachineInstance,
    target_level: int,
) -> bool:
    if target_level <= machine.level:
        return False

    machine_definition = definitions.get_machine(machine.machine_type)
    if machine_definition is None:
        return False

    upgrade_cost = machine_definition.upgrade_costs.get(target_level)
    if upgrade_cost is None:
        return False

    return _has_resources(inventory, upgrade_cost)


def upgrade_machine(
    inventory: dict[str, int],
    definitions: GameDefinitions,
    machine: MachineInstance,
    target_level: int,
) -> bool:
    if not can_upgrade_machine(inventory, definitions, machine, target_level):
        return False

    machine_definition = definitions.get_machine(machine.machine_type)
    upgrade_cost = machine_definition.upgrade_costs[target_level]
    _consume_resources(inventory, upgrade_cost)
    machine.set_level(target_level)
    return True
