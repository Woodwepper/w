from app.engine.construction import build_and_install_machine_from_resources
from app.engine.instances.machine_instance import MachineInstance
from app.engine.instances.module_instance import ModuleInstance
from app.engine.instances.power_network import PowerNetwork
from app.engine.instances.su_source_instance import SUSourceInstance
from app.engine.models.factory_building import FactoryBuilding
from app.engine.models.factory_status import FactoryStatus
from app.engine.models.game_definitions import create_default_definitions
from app.engine.models.world import World
from app.engine.power import calculate_factory_su_required, calculate_machine_su_required
from app.engine.production import process_factory
from app.engine.simulation import tick


PRESS_BUILD_COST = {
    "andesite_alloy": 2,
    "iron_sheet": 1,
}


def configure_manual_definitions(world: World) -> None:
    mechanical_press = world.definitions.get_machine("mechanical_press")
    assert mechanical_press is not None

    assert mechanical_press.build_cost == PRESS_BUILD_COST
    assert mechanical_press.speed_multipliers[2] == 1.25


def create_world(world_id: int = 1, name: str = "Manual Test") -> World:
    world = World(
        id=world_id,
        name=name,
        definitions=create_default_definitions(),
    )
    configure_manual_definitions(world)
    return world


def add_pressing_factory(
    world: World,
    factory_id: int,
    module_id: int,
    machine_count: int,
    *,
    name: str = "Ironworks",
    priority: int = 100,
    level: int = 1,
    active_recipe: str | None = "press_iron_sheet",
    input_amount: int = 20,
    machine_level: int = 1,
) -> tuple[FactoryBuilding, ModuleInstance]:
    factory = FactoryBuilding(
        id=factory_id,
        name=name,
        level=level,
        priority=priority,
    )
    module = ModuleInstance(
        id=module_id,
        module_type="pressing_line",
        active_recipe=active_recipe,
    )

    for index in range(machine_count):
        module.add_machine(
            MachineInstance(
                id=(factory_id * 100) + index,
                machine_type="mechanical_press",
                level=machine_level,
            )
        )

    assert factory.add_module(module, world.definitions)

    if input_amount > 0:
        factory.add_input_item("iron_ingot", input_amount)

    world.add_factory(factory)
    return factory, module


def connect_factory_to_water_wheel(
    world: World,
    factory: FactoryBuilding,
    *,
    source_id: int = 1,
    network_id: int = 1,
) -> None:
    if world.get_su_source(source_id) is None:
        world.add_su_source(
            SUSourceInstance(
                id=source_id,
                source_type="water_wheel",
                name="Water Wheel",
            )
        )

    network = world.get_power_network(network_id)
    if network is None:
        network = PowerNetwork(id=network_id, name="Main Network")
        network.add_source(source_id)
        world.add_power_network(network)

    network.add_consumer("factory", factory.id)


def test_1_world_definitions() -> None:
    definitions = create_default_definitions()
    world = World(id=1, name="Definitions", definitions=definitions)

    assert world.definitions.get_machine("mechanical_press") is not None
    assert world.definitions.get_module("pressing_line") is not None
    assert world.definitions.get_recipe("press_iron_sheet") is not None
    assert world.definitions.get_su_source("water_wheel") is not None
    assert world.definitions.get_factory_level(1) is not None


def test_2_factory_level_limits() -> None:
    world = create_world()
    factory = FactoryBuilding(id=1, name="Ironworks", level=1)

    assert factory.get_module_slot_limit(world.definitions) == 2
    assert factory.get_machine_slot_limit_per_module(world.definitions) == 2


def test_3_build_machine_from_resources() -> None:
    world = create_world()
    world.inventory.update({"andesite_alloy": 5, "iron_sheet": 3})
    factory = FactoryBuilding(id=1, name="Ironworks")
    module = ModuleInstance(id=1, module_type="pressing_line")

    assert factory.add_module(module, world.definitions)
    world.add_factory(factory)

    before_inventory = dict(world.inventory)
    installed = build_and_install_machine_from_resources(
        world,
        factory.id,
        module.id,
        "mechanical_press",
        machine_id=1,
    )

    assert installed
    assert world.inventory["andesite_alloy"] == before_inventory["andesite_alloy"] - 2
    assert world.inventory["iron_sheet"] == before_inventory["iron_sheet"] - 1
    assert len(module.installed_machines) == 1


def test_4_machine_slot_limit() -> None:
    world = create_world()
    world.inventory.update({"andesite_alloy": 10, "iron_sheet": 10})
    factory = FactoryBuilding(id=1, name="Ironworks", level=1)
    module = ModuleInstance(id=1, module_type="pressing_line")

    assert factory.add_module(module, world.definitions)
    world.add_factory(factory)

    first = build_and_install_machine_from_resources(
        world, factory.id, module.id, "mechanical_press", machine_id=1
    )
    second = build_and_install_machine_from_resources(
        world, factory.id, module.id, "mechanical_press", machine_id=2
    )
    third = build_and_install_machine_from_resources(
        world, factory.id, module.id, "mechanical_press", machine_id=3
    )

    assert first
    assert second
    assert not third
    assert len(module.installed_machines) == 2


def test_5_individual_machine_production() -> None:
    world = create_world()
    factory, _module = add_pressing_factory(
        world,
        factory_id=1,
        module_id=1,
        machine_count=2,
    )
    connect_factory_to_water_wheel(world, factory)

    tick(world, 10)

    assert factory.get_input_amount("iron_ingot") == 16
    assert factory.get_output_amount("iron_sheet") == 4


def test_6_upgraded_machine_speed_and_su() -> None:
    world = create_world()

    level_1_factory, _level_1_module = add_pressing_factory(
        world,
        factory_id=1,
        module_id=1,
        machine_count=1,
        machine_level=1,
    )
    level_2_factory, _level_2_module = add_pressing_factory(
        world,
        factory_id=2,
        module_id=2,
        machine_count=1,
        machine_level=2,
    )

    process_factory(world, level_1_factory, 20)
    process_factory(world, level_2_factory, 20)

    level_1_machine = level_1_factory.modules[0].installed_machines[0]
    level_2_machine = level_2_factory.modules[0].installed_machines[0]

    assert level_1_factory.get_output_amount("iron_sheet") == 4
    assert level_2_factory.get_output_amount("iron_sheet") == 5
    assert calculate_machine_su_required(world, level_1_machine) == calculate_machine_su_required(
        world,
        level_2_machine,
    )


def test_7_local_su_sufficient() -> None:
    world = create_world()
    factory, _module = add_pressing_factory(
        world,
        factory_id=1,
        module_id=1,
        machine_count=1,
    )
    connect_factory_to_water_wheel(world, factory)

    assert calculate_factory_su_required(world, factory) < 4096

    tick(world, 10)

    assert factory.status == FactoryStatus.WORKING
    assert factory.get_output_amount("iron_sheet") == 2


def test_8_local_su_priority() -> None:
    world = create_world()
    factory_a, _module_a = add_pressing_factory(
        world,
        factory_id=1,
        module_id=1,
        machine_count=3,
        level=2,
        name="Factory A",
        priority=10,
    )
    factory_b, _module_b = add_pressing_factory(
        world,
        factory_id=2,
        module_id=2,
        machine_count=2,
        level=2,
        name="Factory B",
        priority=100,
    )
    connect_factory_to_water_wheel(world, factory_a)
    connect_factory_to_water_wheel(world, factory_b)

    assert calculate_factory_su_required(world, factory_a) == 3072
    assert calculate_factory_su_required(world, factory_b) == 2048

    tick(world, 10)

    assert factory_a.status == FactoryStatus.WORKING
    assert factory_b.status == FactoryStatus.UNDERPOWERED
    assert factory_a.get_output_amount("iron_sheet") == 6
    assert factory_b.get_output_amount("iron_sheet") == 0
    assert all(
        machine.progress == 0
        for module in factory_b.modules
        for machine in module.installed_machines
    )


def test_9_invalid_recipe() -> None:
    world = create_world()
    factory, _module = add_pressing_factory(
        world,
        factory_id=1,
        module_id=1,
        machine_count=1,
        active_recipe="smelt_crushed_iron",
    )
    factory.add_input_item("crushed_iron", 10)
    connect_factory_to_water_wheel(world, factory)

    tick(world, 10)

    assert factory.status == FactoryStatus.INVALID_RECIPE
    assert factory.get_output_amount("iron_ingot") == 0


def test_10_missing_machine() -> None:
    world = create_world()
    factory, _module = add_pressing_factory(
        world,
        factory_id=1,
        module_id=1,
        machine_count=0,
        active_recipe="press_iron_sheet",
    )
    connect_factory_to_water_wheel(world, factory)

    tick(world, 10)

    assert factory.status == FactoryStatus.MISSING_MACHINE
    assert factory.get_output_amount("iron_sheet") == 0


def test_11_missing_inputs_do_not_accumulate_progress() -> None:
    world = create_world()
    factory, module = add_pressing_factory(
        world,
        factory_id=1,
        module_id=1,
        machine_count=1,
        input_amount=0,
    )
    connect_factory_to_water_wheel(world, factory)
    machine = module.installed_machines[0]

    tick(world, 20)

    assert machine.status == FactoryStatus.MISSING_INPUT
    assert machine.progress == 0
    assert factory.get_output_amount("iron_sheet") == 0


def test_12_inputs_after_missing_do_not_instantly_produce() -> None:
    world = create_world()
    factory, module = add_pressing_factory(
        world,
        factory_id=1,
        module_id=1,
        machine_count=1,
        input_amount=0,
    )
    connect_factory_to_water_wheel(world, factory)
    machine = module.installed_machines[0]

    tick(world, 20)
    factory.add_input_item("iron_ingot", 1)
    tick(world, 1)

    assert machine.status == FactoryStatus.WORKING
    assert machine.progress == 1
    assert factory.get_input_amount("iron_ingot") == 1
    assert factory.get_output_amount("iron_sheet") == 0


def test_13_invalid_recipe_clears_machine_statuses() -> None:
    world = create_world()
    factory, module = add_pressing_factory(
        world,
        factory_id=1,
        module_id=1,
        machine_count=1,
    )
    connect_factory_to_water_wheel(world, factory)
    machine = module.installed_machines[0]

    tick(world, 1)
    assert machine.status == FactoryStatus.WORKING

    module.set_active_recipe("smelt_crushed_iron")
    tick(world, 1)

    assert module.status == FactoryStatus.INVALID_RECIPE
    assert machine.status == FactoryStatus.INVALID_RECIPE
    assert factory.get_output_amount("iron_ingot") == 0


def test_14_default_machine_definitions_are_complete() -> None:
    world = create_world()
    mechanical_press = world.definitions.get_machine("mechanical_press")
    assert mechanical_press is not None

    assert mechanical_press.build_cost == PRESS_BUILD_COST
    assert mechanical_press.upgrade_costs[2]
    assert mechanical_press.upgrade_costs[3]
    assert mechanical_press.speed_multipliers[1] == 1.0
    assert mechanical_press.speed_multipliers[2] == 1.25
    assert mechanical_press.speed_multipliers[3] == 1.5


def test_15_world_to_dict_uses_su_required() -> None:
    world = create_world()
    world.su_required = 1234

    data = world.to_dict()

    assert data["su_required"] == 1234
    assert data["su_requiered"] == 1234


def test_16_missing_inputs_preserve_real_progress_only() -> None:
    world = create_world()
    factory, module = add_pressing_factory(
        world,
        factory_id=1,
        module_id=1,
        machine_count=1,
        input_amount=1,
    )
    connect_factory_to_water_wheel(world, factory)
    machine = module.installed_machines[0]

    tick(world, 2)
    assert machine.progress == 2
    assert factory.get_output_amount("iron_sheet") == 0

    assert factory.remove_input_item("iron_ingot", 1)
    tick(world, 20)
    assert machine.progress == 2

    factory.add_input_item("iron_ingot", 1)
    tick(world, 2)

    assert machine.progress == 4
    assert factory.get_input_amount("iron_ingot") == 1
    assert factory.get_output_amount("iron_sheet") == 0


TESTS = [
    ("Test 1: mundo con definiciones", test_1_world_definitions),
    ("Test 2: fabrica con nivel", test_2_factory_level_limits),
    ("Test 3: construir e instalar maquina", test_3_build_machine_from_resources),
    ("Test 4: limite de maquinas", test_4_machine_slot_limit),
    ("Test 5: produccion individual", test_5_individual_machine_production),
    ("Test 6: maquina mejorada", test_6_upgraded_machine_speed_and_su),
    ("Test 7: SU local suficiente", test_7_local_su_sufficient),
    ("Test 8: SU local insuficiente por prioridad", test_8_local_su_priority),
    ("Test 9: receta invalida", test_9_invalid_recipe),
    ("Test 10: missing machine", test_10_missing_machine),
    (
        "Test 11: sin inputs no acumula progress",
        test_11_missing_inputs_do_not_accumulate_progress,
    ),
    (
        "Test 12: inputs tardios no producen instantaneo",
        test_12_inputs_after_missing_do_not_instantly_produce,
    ),
    (
        "Test 13: receta invalida limpia maquinas",
        test_13_invalid_recipe_clears_machine_statuses,
    ),
    (
        "Test 14: default mechanical_press completo",
        test_14_default_machine_definitions_are_complete,
    ),
    ("Test 15: World.to_dict usa su_required", test_15_world_to_dict_uses_su_required),
    (
        "Test 16: sin inputs conserva solo progreso real",
        test_16_missing_inputs_preserve_real_progress_only,
    ),
]


def main() -> int:
    failures = []

    for name, test in TESTS:
        try:
            test()
        except AssertionError as exc:
            failures.append((name, str(exc)))
            print(f"FAIL - {name}")
        else:
            print(f"PASS - {name}")

    print(f"\nResult: {len(TESTS) - len(failures)}/{len(TESTS)} tests passed")

    if failures:
        print("\nFailures:")
        for name, message in failures:
            suffix = f": {message}" if message else ""
            print(f"- {name}{suffix}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
