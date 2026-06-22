from app.engine.core.statuses import FactoryStatus, ProducerStatus, SUProducerStatus
from app.engine.core.world import World
from app.engine.entities.factory_building import FactoryBuilding
from app.engine.entities.module_instance import ModuleInstance
from app.engine.entities.power_network import PowerNetwork
from app.engine.entities.producer_building import ProducerBuilding
from app.engine.entities.resource_node import ResourceNode
from app.engine.entities.su_producer_building import SUProducerBuilding
from app.engine.systems.construction import (
    build_machine_to_inventory,
    install_machine_from_inventory_to_module,
    install_machine_from_inventory_to_producer,
    uninstall_machine_from_module_to_inventory,
)
from app.engine.systems.power import calculate_machine_su_required
from app.engine.systems.simulation import tick
from app.engine.systems.su_producers import calculate_su_producer_output


def add_items(world: World, items: dict[str, int]) -> None:
    for item_id, amount in items.items():
        world.inventory.add_normal_item(item_id, amount)


def add_river_power(world: World, su_producer_id: int = 1) -> SUProducerBuilding:
    su_producer = SUProducerBuilding(
        id=su_producer_id,
        name="River Power",
        producer_type="river_power_complex",
    )
    su_producer.add_unit("water_wheel_unit", 4)
    world.add_su_producer(su_producer)
    return su_producer


def connect(world: World, consumers: list[tuple[str, int]]) -> None:
    add_river_power(world)
    network = PowerNetwork(id=1, name="Grid")
    network.add_source(1)
    for consumer_type, consumer_id in consumers:
        network.add_consumer(consumer_type, consumer_id)
    world.add_power_network(network)


def test_flow_a_factory_with_su_producer_and_inventory_inputs() -> None:
    world = World(id=1, name="Factory Flow")
    add_items(
        world,
        {
            "andesite_alloy": 10,
            "iron_sheet": 10,
            "iron_ingot": 20,
        },
    )
    factory = FactoryBuilding(id=1, name="Ironworks")
    module = ModuleInstance(
        id=1,
        module_type="pressing_line",
        active_recipe="press_iron_sheet",
    )
    assert factory.add_module(module, world.definitions)
    world.add_factory(factory)

    assert build_machine_to_inventory(world.inventory, world.definitions, "mechanical_press")
    assert build_machine_to_inventory(world.inventory, world.definitions, "mechanical_press")
    assert install_machine_from_inventory_to_module(world, 1, 1, "mechanical_press", 1)
    assert install_machine_from_inventory_to_module(world, 1, 1, "mechanical_press", 2)
    assert world.inventory.remove_normal_item("iron_ingot", 20)
    factory.add_input_item("iron_ingot", 20)
    connect(world, [("factory", factory.id)])

    tick(world, 10)

    assert factory.status == FactoryStatus.WORKING
    assert factory.get_input_amount("iron_ingot") == 16
    assert factory.get_output_amount("iron_sheet") == 4


def test_flow_b_resource_producer_with_su_producer() -> None:
    world = World(id=1, name="Producer Flow")
    node = ResourceNode(
        id=1,
        node_type="iron_deposit",
        name="Iron Deposit",
        x=0,
        y=0,
        remaining_amount=1000,
    )
    producer = ProducerBuilding(
        id=1,
        name="Iron Mine",
        producer_type="mine",
        resource_node_id=node.id,
    )
    world.add_resource_node(node)
    world.add_producer(producer)
    add_items(world, {"andesite_alloy": 6, "iron_sheet": 4, "shaft": 2})

    assert build_machine_to_inventory(world.inventory, world.definitions, "mechanical_drill")
    assert build_machine_to_inventory(world.inventory, world.definitions, "mechanical_drill")
    assert install_machine_from_inventory_to_producer(world, 1, "mechanical_drill", 1)
    assert install_machine_from_inventory_to_producer(world, 1, "mechanical_drill", 2)
    connect(world, [("producer", producer.id)])

    tick(world, 10)

    assert producer.status == ProducerStatus.WORKING
    assert producer.get_output_amount("raw_iron") == 4
    assert node.remaining_amount == 996


def test_flow_c_entity_stack_install_uninstall() -> None:
    world = World(id=1, name="Entity Flow")
    add_items(world, {"andesite_alloy": 2, "iron_sheet": 1})
    factory = FactoryBuilding(id=1, name="Ironworks")
    module = ModuleInstance(id=1, module_type="pressing_line")
    assert factory.add_module(module, world.definitions)
    world.add_factory(factory)

    assert build_machine_to_inventory(
        world.inventory,
        world.definitions,
        "mechanical_press",
        level=3,
        metadata={"line": "A"},
    )
    assert install_machine_from_inventory_to_module(world, 1, 1, "mechanical_press", 1)
    machine = module.installed_machines[0]
    machine.progress = 4.5
    assert uninstall_machine_from_module_to_inventory(world, 1, 1, machine.id)

    assert module.installed_machines == []
    stack = world.inventory.find_entity_stack("mechanical_press", "machine")
    assert stack is not None
    assert stack.entity_data["level"] == 3
    assert stack.entity_data["metadata"]["line"] == "A"
    assert "progress" not in stack.entity_data


def test_flow_d_steam_su_producer_consumes_input_once_per_tick() -> None:
    world = World(id=1, name="Steam Flow")
    su_producer = SUProducerBuilding(
        id=1,
        name="Steam Power",
        producer_type="steam_power_complex",
    )
    su_producer.add_unit("steam_engine_unit", 1)
    su_producer.add_input_item("coal", 2)
    world.add_su_producer(su_producer)

    assert calculate_su_producer_output(world, su_producer) == 4096
    assert calculate_su_producer_output(world, su_producer) == 4096
    assert su_producer.get_input_amount("coal") == 2

    network = PowerNetwork(id=1, name="Grid")
    network.add_source(1)
    world.add_power_network(network)
    tick(world, 1)

    assert su_producer.status == SUProducerStatus.ACTIVE
    assert su_producer.get_input_amount("coal") == 1

    tick(world, 1)
    assert su_producer.status == SUProducerStatus.ACTIVE
    assert su_producer.get_input_amount("coal") == 0

    tick(world, 1)
    assert su_producer.status == SUProducerStatus.MISSING_INPUT
    assert su_producer.get_input_amount("coal") == 0


def test_flow_e_save_load_keeps_definitions_and_continues() -> None:
    world = World(id=1, name="Save Flow")
    add_items(world, {"andesite_alloy": 4, "iron_sheet": 2, "iron_ingot": 10})
    factory = FactoryBuilding(id=1, name="Ironworks")
    module = ModuleInstance(
        id=1,
        module_type="pressing_line",
        active_recipe="press_iron_sheet",
    )
    assert factory.add_module(module, world.definitions)
    world.add_factory(factory)
    assert build_machine_to_inventory(world.inventory, world.definitions, "mechanical_press")
    assert install_machine_from_inventory_to_module(world, 1, 1, "mechanical_press", 1)
    factory.add_input_item("iron_ingot", 10)
    connect(world, [("factory", factory.id)])

    restored = World.from_dict(world.to_dict())
    tick(restored, 10)

    assert restored.definitions.get_recipe("press_iron_sheet") is not None
    assert restored.factories[0].get_output_amount("iron_sheet") == 2
    machine = restored.factories[0].modules[0].installed_machines[0]
    assert calculate_machine_su_required(restored, machine) == 1024


def test_flow_f_raw_iron_to_iron_sheet_content_chain() -> None:
    world = World(id=1, name="Iron Chain")
    add_items(
        world,
        {
            "andesite_alloy": 20,
            "iron_sheet": 6,
            "shaft": 4,
            "brick": 4,
            "copper_sheet": 1,
            "cogwheel": 2,
        },
    )

    factory = FactoryBuilding(id=1, name="Ironworks", level=2)
    crushing = ModuleInstance(id=1, module_type="crushing_line", active_recipe="crush_raw_iron")
    smelting = ModuleInstance(id=2, module_type="smelting_line", active_recipe="smelt_crushed_iron")
    pressing = ModuleInstance(id=3, module_type="pressing_line", active_recipe="press_iron_sheet")
    assert factory.add_module(crushing, world.definitions)
    assert factory.add_module(smelting, world.definitions)
    assert factory.add_module(pressing, world.definitions)
    world.add_factory(factory)

    assert build_machine_to_inventory(world.inventory, world.definitions, "crushing_wheel")
    assert build_machine_to_inventory(world.inventory, world.definitions, "mechanical_smelter")
    assert build_machine_to_inventory(world.inventory, world.definitions, "mechanical_press")
    assert install_machine_from_inventory_to_module(world, 1, 1, "crushing_wheel", 1)
    assert install_machine_from_inventory_to_module(world, 1, 2, "mechanical_smelter", 2)
    assert install_machine_from_inventory_to_module(world, 1, 3, "mechanical_press", 3)

    factory.add_input_item("raw_iron", 1)
    connect(world, [("factory", factory.id)])
    world.su_producers[0].add_unit("water_wheel_unit", 2)

    tick(world, 5)
    assert factory.remove_output_item("crushed_raw_iron", 1)
    factory.add_input_item("crushed_raw_iron", 1)
    tick(world, 5)
    assert factory.remove_output_item("iron_ingot", 1)
    factory.add_input_item("iron_ingot", 1)
    tick(world, 5)

    assert factory.get_output_amount("iron_sheet") == 1


TESTS = [
    ("Flow A: factory con SUProducer", test_flow_a_factory_with_su_producer_and_inventory_inputs),
    ("Flow B: producer con SUProducer", test_flow_b_resource_producer_with_su_producer),
    ("Flow C: EntityStack instala/desinstala", test_flow_c_entity_stack_install_uninstall),
    ("Flow D: steam consume input", test_flow_d_steam_su_producer_consumes_input_once_per_tick),
    ("Flow E: save/load", test_flow_e_save_load_keeps_definitions_and_continues),
    ("Flow F: raw iron a iron sheet", test_flow_f_raw_iron_to_iron_sheet_content_chain),
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
