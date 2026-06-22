from typing import Any

from app.engine.entities.machine_instance import MachineInstance
from app.engine.entities.module_instance import ModuleInstance
from app.engine.entities.factory_building import FactoryBuilding
from app.engine.definitions.game_definitions import GameDefinitions
from app.engine.core.world import World
from app.engine.inventory.entity_stack import EntityStack
from app.engine.inventory.inventory import Inventory
from app.engine.systems.machine_hosts import (
    can_install_machine_on_host,
    create_machine_instance,
)


def _has_resources(inventory, cost: dict[str, int]) -> bool:
    for item_id, amount in cost.items():
        if inventory.get(item_id, 0) < amount:
            return False
    return True


def _consume_resources(inventory, cost: dict[str, int]) -> None:
    for item_id, amount in cost.items():
        remaining_amount = inventory.get(item_id, 0) - amount
        if remaining_amount <= 0:
            inventory.pop(item_id, None)
        else:
            inventory[item_id] = remaining_amount


def can_build_machine_from_resources(
    inventory,
    definitions: GameDefinitions,
    machine_type: str,
) -> bool:
    machine_definition = definitions.get_machine(machine_type)
    if machine_definition is None:
        return False

    return _has_resources(inventory, machine_definition.build_cost)


def build_machine_from_resources(
    inventory,
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

    return create_machine_instance(machine_type, machine_id, level, metadata)


def build_machine_to_inventory(
    inventory: Inventory,
    definitions: GameDefinitions,
    machine_type: str,
    level: int = 1,
    metadata: dict[str, Any] | None = None,
) -> bool:
    machine_definition = definitions.get_machine(machine_type)
    object_definition = definitions.get_object(machine_type)
    if (
        machine_definition is None
        or object_definition is None
        or object_definition.stack_kind != "entity"
        or object_definition.entity_type != "machine"
    ):
        return False

    if not _has_resources(inventory, machine_definition.build_cost):
        return False

    _consume_resources(inventory, machine_definition.build_cost)
    entity_data = dict(object_definition.default_entity_data)
    entity_data["level"] = max(1, level)
    entity_data["metadata"] = dict(metadata or {})
    inventory.add_entity_stack(
        EntityStack(
            object_id=machine_type,
            entity_type="machine",
            amount=1,
            entity_data=entity_data,
        )
    )
    return True


def add_machine_to_inventory(
    inventory: Inventory,
    machine: MachineInstance,
) -> None:
    inventory.add_entity_stack(
        EntityStack(
            object_id=machine.machine_type,
            entity_type="machine",
            amount=1,
            entity_data={
                "level": machine.level,
                "metadata": dict(machine.metadata),
            },
        )
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

    return can_install_machine_on_host(
        machine=machine,
        definitions=definitions,
        allowed_machine_types=module_definition.allowed_machine_types,
        installed_machines=module.installed_machines,
        slot_limit=factory.get_machine_slot_limit_per_module(definitions),
        get_existing_machine=module.get_machine,
    )


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

    proposed_machine = create_machine_instance(
        machine_type,
        machine_id,
        level,
        metadata,
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
    inventory,
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
    inventory,
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
