from app.engine.entities.machine_instance import MachineInstance
from app.engine.entities.module_instance import ModuleInstance
from app.engine.entities.factory_building import FactoryBuilding
from app.engine.core.statuses import FactoryStatus
from app.engine.core.statuses import MachineStatus
from app.engine.definitions.recipe_definition import Recipe
from app.engine.core.world import World


def process_factory(
    world: World,
    factory: FactoryBuilding,
    seconds: float,
) -> None:
    if seconds <= 0:
        return

    if factory.status == FactoryStatus.UNDERPOWERED:
        return

    if not factory.modules:
        factory.status = FactoryStatus.IDLE
        return

    for module in factory.modules:
        process_module(world, factory, module, seconds)

    update_factory_status_from_modules(factory)


def process_module(
    world: World,
    factory: FactoryBuilding,
    module: ModuleInstance,
    seconds: float,
) -> None:
    if seconds <= 0:
        return

    if module.active_recipe is None:
        module.status = FactoryStatus.IDLE
        for machine in module.installed_machines:
            machine.status = MachineStatus.IDLE
        return

    recipe = world.definitions.get_recipe(module.active_recipe)
    if recipe is None:
        module.status = FactoryStatus.INVALID_RECIPE
        set_module_machines_status(module, MachineStatus.INVALID_RECIPE)
        return

    module_definition = world.definitions.get_module(module.module_type)
    if module_definition is None:
        module.status = FactoryStatus.INVALID_RECIPE
        set_module_machines_status(module, MachineStatus.INVALID_RECIPE)
        return

    if recipe.id not in module_definition.allowed_recipes:
        module.status = FactoryStatus.INVALID_RECIPE
        set_module_machines_status(module, MachineStatus.INVALID_RECIPE)
        return

    compatible_machines = [
        machine
        for machine in module.installed_machines
        if machine_can_process_recipe(world, machine, recipe)
    ]

    if not compatible_machines:
        module.status = FactoryStatus.MISSING_MACHINE
        return

    for machine in module.installed_machines:
        if machine not in compatible_machines:
            machine.status = MachineStatus.IDLE

    for machine in compatible_machines:
        process_machine(world, factory, module, machine, recipe, seconds)

    update_module_status_from_machines(module, compatible_machines)


def process_machine(
    world: World,
    factory: FactoryBuilding,
    module: ModuleInstance,
    machine: MachineInstance,
    recipe: Recipe,
    seconds: float,
) -> None:
    if seconds <= 0:
        return

    if machine.status == MachineStatus.UNDERPOWERED:
        return

    machine_definition = world.definitions.get_machine(machine.machine_type)
    if machine_definition is None:
        machine.status = MachineStatus.MISSING_MACHINE
        return

    speed_multiplier = machine_definition.get_speed_multiplier(machine.level)
    if speed_multiplier <= 0:
        speed_multiplier = 1.0

    effective_duration = recipe.duration / speed_multiplier
    if effective_duration <= 0:
        machine.status = MachineStatus.INVALID_RECIPE
        return

    if not factory_has_required_inputs(factory, recipe):
        machine.status = MachineStatus.MISSING_INPUT
        return

    remaining_seconds = seconds
    produced_cycles = 0

    while remaining_seconds > 0:
        if not factory_has_required_inputs(factory, recipe):
            break

        time_to_complete = effective_duration - machine.progress

        if remaining_seconds < time_to_complete:
            machine.progress += remaining_seconds
            machine.status = MachineStatus.WORKING
            return

        remaining_seconds -= time_to_complete
        consume_recipe_inputs(factory, recipe)
        produce_recipe_outputs(factory, recipe)
        machine.progress = 0.0
        produced_cycles += 1

    if produced_cycles > 0:
        machine.status = MachineStatus.WORKING
        return

    machine.status = MachineStatus.MISSING_INPUT


def machine_can_process_recipe(
    world: World,
    machine: MachineInstance,
    recipe: Recipe,
) -> bool:
    machine_definition = world.definitions.get_machine(machine.machine_type)
    if machine_definition is None:
        return False

    if machine.machine_type not in recipe.required_machines:
        return False

    return recipe.id in machine_definition.allowed_recipes


def factory_has_required_inputs(
    factory: FactoryBuilding,
    recipe: Recipe,
) -> bool:
    for item_id, amount in recipe.input_items.items():
        if factory.get_input_amount(item_id) < amount:
            return False

    return True


def consume_recipe_inputs(
    factory: FactoryBuilding,
    recipe: Recipe,
) -> None:
    for item_id, amount in recipe.input_items.items():
        factory.remove_input_item(item_id, amount)


def produce_recipe_outputs(
    factory: FactoryBuilding,
    recipe: Recipe,
) -> None:
    for item_id, amount in recipe.output_items.items():
        factory.add_output_item(item_id, amount)


def set_module_machines_status(
    module: ModuleInstance,
    status: MachineStatus,
) -> None:
    for machine in module.installed_machines:
        machine.status = status


def update_module_status_from_machines(
    module: ModuleInstance,
    compatible_machines: list[MachineInstance],
) -> None:
    machine_statuses = [machine.status for machine in compatible_machines]

    if any(status == MachineStatus.WORKING for status in machine_statuses):
        module.status = FactoryStatus.WORKING
        return

    if any(status == MachineStatus.MISSING_INPUT for status in machine_statuses):
        module.status = FactoryStatus.MISSING_INPUT
        return

    if any(status == MachineStatus.MISSING_MACHINE for status in machine_statuses):
        module.status = FactoryStatus.MISSING_MACHINE
        return

    if any(status == MachineStatus.INVALID_RECIPE for status in machine_statuses):
        module.status = FactoryStatus.INVALID_RECIPE
        return

    if all(status == MachineStatus.IDLE for status in machine_statuses):
        module.status = FactoryStatus.IDLE
        return

    module.status = FactoryStatus.IDLE


def update_factory_status_from_modules(factory: FactoryBuilding) -> None:
    if not factory.modules:
        factory.status = FactoryStatus.IDLE
        return

    module_statuses = [module.status for module in factory.modules]

    if any(status == FactoryStatus.WORKING for status in module_statuses):
        factory.status = FactoryStatus.WORKING
        return

    if all(status == FactoryStatus.IDLE for status in module_statuses):
        factory.status = FactoryStatus.IDLE
        return

    if any(status == FactoryStatus.MISSING_INPUT for status in module_statuses):
        factory.status = FactoryStatus.MISSING_INPUT
        return

    if any(status == FactoryStatus.MISSING_MACHINE for status in module_statuses):
        factory.status = FactoryStatus.MISSING_MACHINE
        return

    if any(status == FactoryStatus.INVALID_RECIPE for status in module_statuses):
        factory.status = FactoryStatus.INVALID_RECIPE
        return

    factory.status = FactoryStatus.IDLE
