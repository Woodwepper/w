from app.engine.core.statuses import FactoryStatus, ProducerStatus, SUProducerStatus
from app.engine.core.world import World
from app.engine.entities.factory_building import FactoryBuilding
from app.engine.entities.machine_instance import MachineInstance
from app.engine.entities.module_instance import ModuleInstance
from app.engine.entities.power_network import PowerNetwork
from app.engine.entities.producer_building import ProducerBuilding
from app.engine.entities.resource_node import ResourceNode
from app.engine.entities.su_producer_building import SUProducerBuilding
from app.engine.systems.power import calculate_network_su_output
from app.engine.systems.simulation import tick


def create_world() -> World:
    return World(id=1, name="SU Producer Test")


def create_river_power(world: World, *, unit_count: int = 4) -> SUProducerBuilding:
    su_producer = SUProducerBuilding(
        id=1,
        name="River Power",
        producer_type="river_power_complex",
    )
    if unit_count > 0:
        su_producer.add_unit("water_wheel_unit", unit_count)
    world.add_su_producer(su_producer)
    return su_producer


def create_pressing_factory(world: World) -> FactoryBuilding:
    factory = FactoryBuilding(id=1, name="Ironworks")
    module = ModuleInstance(
        id=1,
        module_type="pressing_line",
        active_recipe="press_iron_sheet",
    )
    module.add_machine(MachineInstance(id=1, machine_type="mechanical_press"))
    assert factory.add_module(module, world.definitions)
    factory.add_input_item("iron_ingot", 10)
    world.add_factory(factory)
    return factory


def create_mine(world: World) -> ProducerBuilding:
    node = ResourceNode(
        id=1,
        node_type="iron_deposit",
        name="Iron Deposit",
        x=0,
        y=0,
        remaining_amount=1000,
    )
    world.add_resource_node(node)
    producer = ProducerBuilding(
        id=1,
        name="Iron Mine",
        producer_type="mine",
        resource_node_id=node.id,
    )
    producer.add_machine(MachineInstance(id=101, machine_type="mechanical_drill"))
    producer.add_machine(MachineInstance(id=102, machine_type="mechanical_drill"))
    world.add_producer(producer)
    return producer


def connect_power(
    world: World,
    consumers: list[tuple[str, int]],
) -> PowerNetwork:
    network = PowerNetwork(id=1, name="New Grid")
    network.add_source(1)
    for consumer_type, consumer_id in consumers:
        network.add_consumer(consumer_type, consumer_id)
    world.add_power_network(network)
    return network


def test_1_su_producer_generates_su() -> None:
    world = create_world()
    su_producer = create_river_power(world)
    network = connect_power(world, [])

    assert calculate_network_su_output(world, network) == 4096
    assert su_producer.status == SUProducerStatus.ACTIVE


def test_2_su_producer_feeds_factory() -> None:
    world = create_world()
    create_river_power(world)
    factory = create_pressing_factory(world)
    connect_power(world, [("factory", factory.id)])

    tick(world, 10)

    assert factory.status == FactoryStatus.WORKING
    assert factory.get_output_amount("iron_sheet") == 2
    assert world.su_produced == 4096


def test_3_su_producer_feeds_resource_producer() -> None:
    world = create_world()
    create_river_power(world)
    producer = create_mine(world)
    connect_power(world, [("producer", producer.id)])

    tick(world, 10)

    assert producer.status == ProducerStatus.WORKING
    assert producer.get_output_amount("raw_iron") == 4


def test_4_su_producer_without_units_does_not_generate() -> None:
    world = create_world()
    su_producer = create_river_power(world, unit_count=0)
    factory = create_pressing_factory(world)
    connect_power(world, [("factory", factory.id)])

    tick(world, 10)

    assert su_producer.status == SUProducerStatus.MISSING_UNIT
    assert factory.status == FactoryStatus.UNDERPOWERED
    assert factory.get_output_amount("iron_sheet") == 0


def test_5_su_producer_missing_input_does_not_generate() -> None:
    world = create_world()
    su_producer = SUProducerBuilding(
        id=1,
        name="Steam Power",
        producer_type="steam_power_complex",
    )
    su_producer.add_unit("steam_engine_unit", 1)
    world.add_su_producer(su_producer)
    network = connect_power(world, [])

    assert calculate_network_su_output(world, network) == 0
    assert su_producer.status == SUProducerStatus.MISSING_INPUT

    su_producer.add_input_item("coal", 1)

    assert calculate_network_su_output(world, network) == 4096
    assert su_producer.status == SUProducerStatus.ACTIVE


def test_6_su_producer_roundtrip() -> None:
    world = create_world()
    create_river_power(world)
    connect_power(world, [])

    restored = World.from_dict(world.to_dict())

    assert len(restored.su_producers) == 1
    assert restored.su_producers[0].get_unit_amount("water_wheel_unit") == 4
    assert restored.power_networks[0].su_producer_ids[0] == 1


TESTS = [
    ("Test 1: SUProducer produce SU", test_1_su_producer_generates_su),
    ("Test 2: SUProducer alimenta factory", test_2_su_producer_feeds_factory),
    (
        "Test 3: SUProducer alimenta producer",
        test_3_su_producer_feeds_resource_producer,
    ),
    (
        "Test 4: SUProducer sin unidades",
        test_4_su_producer_without_units_does_not_generate,
    ),
    (
        "Test 5: SUProducer con input faltante",
        test_5_su_producer_missing_input_does_not_generate,
    ),
    ("Test 6: SUProducer serializa", test_6_su_producer_roundtrip),
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
