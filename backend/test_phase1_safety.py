from app.engine.systems.construction import can_install_machine_in_module
from app.engine.core.statuses import MachineStatus
from app.engine.entities.machine_instance import MachineInstance
from app.engine.entities.module_instance import ModuleInstance
from app.engine.entities.power_network import PowerNetwork
from app.engine.entities.su_source_instance import SUSourceInstance
from app.engine.entities.factory_building import FactoryBuilding
from app.engine.core.statuses import FactoryStatus
from app.engine.entities.producer_building import ProducerBuilding
from app.engine.core.statuses import ProducerStatus
from app.engine.entities.resource_node import ResourceNode
from app.engine.core.world import World
from app.engine.systems.producers import can_install_machine_in_producer
from app.engine.systems.simulation import tick


def create_world(name: str = "Phase 1 Safety") -> World:
    return World(id=1, name=name)


def create_pressing_factory(
    world: World,
    *,
    factory_id: int = 1,
    module_id: int = 1,
    machine_count: int = 2,
    priority: int = 100,
    level: int = 1,
    input_amount: int = 20,
) -> tuple[FactoryBuilding, ModuleInstance]:
    factory = FactoryBuilding(
        id=factory_id,
        name=f"Ironworks {factory_id}",
        level=level,
        priority=priority,
    )
    module = ModuleInstance(
        id=module_id,
        module_type="pressing_line",
        active_recipe="press_iron_sheet",
    )

    for index in range(machine_count):
        module.add_machine(
            MachineInstance(
                id=(factory_id * 100) + index,
                machine_type="mechanical_press",
            )
        )

    assert factory.add_module(module, world.definitions)
    factory.add_input_item("iron_ingot", input_amount)
    world.add_factory(factory)
    return factory, module


def create_iron_node(
    world: World,
    *,
    node_id: int = 1,
    remaining_amount: int = 1000,
    required_machine_level: int = 1,
) -> ResourceNode:
    node = ResourceNode(
        id=node_id,
        node_type="iron_deposit",
        name=f"Iron Deposit {node_id}",
        x=4,
        y=2,
        richness=1,
        hardness=1.0,
        required_machine_level=required_machine_level,
        remaining_amount=remaining_amount,
        infinite=False,
    )
    world.add_resource_node(node)
    return node


def create_mine(
    world: World,
    node: ResourceNode,
    *,
    producer_id: int = 1,
    machine_count: int = 2,
    priority: int = 100,
) -> ProducerBuilding:
    producer = ProducerBuilding(
        id=producer_id,
        name=f"Iron Mine {producer_id}",
        producer_type="mine",
        resource_node_id=node.id,
        x=node.x,
        y=node.y,
        level=1,
        priority=priority,
    )

    for index in range(machine_count):
        producer.add_machine(
            MachineInstance(
                id=(producer_id * 1000) + index,
                machine_type="mechanical_drill",
            )
        )

    world.add_producer(producer)
    return producer


def connect_power(
    world: World,
    consumers: list[tuple[str, int]],
    *,
    source_id: int = 1,
    network_id: int = 1,
) -> PowerNetwork:
    world.add_su_source(
        SUSourceInstance(
            id=source_id,
            source_type="water_wheel",
            name=f"Water Wheel {source_id}",
        )
    )
    network = PowerNetwork(id=network_id, name=f"Network {network_id}")
    network.add_source(source_id)
    for consumer_type, consumer_id in consumers:
        network.add_consumer(consumer_type, consumer_id)
    world.add_power_network(network)
    return network


def test_1_factory_production_basic() -> None:
    world = create_world()
    factory, module = create_pressing_factory(world)
    connect_power(world, [("factory", factory.id)])

    tick(world, 10)

    assert factory.status == FactoryStatus.WORKING
    assert factory.get_input_amount("iron_ingot") == 16
    assert factory.get_output_amount("iron_sheet") == 4
    assert len(module.installed_machines) == 2
    assert module.installed_machines[0] is not module.installed_machines[1]
    assert all(machine.progress == 0 for machine in module.installed_machines)
    assert all(machine.status == MachineStatus.WORKING for machine in module.installed_machines)


def test_2_producer_resource_node_basic() -> None:
    world = create_world()
    node = create_iron_node(world)
    producer = create_mine(world, node)
    connect_power(world, [("producer", producer.id)])

    tick(world, 10)

    assert producer.status == ProducerStatus.WORKING
    assert producer.get_output_amount("raw_iron") == 4
    assert node.remaining_amount == 996
    assert len(producer.installed_machines) == 2
    assert producer.installed_machines[0] is not producer.installed_machines[1]
    assert all(machine.progress == 0 for machine in producer.installed_machines)
    assert all(machine.status == MachineStatus.WORKING for machine in producer.installed_machines)


def test_3_power_network_sufficient() -> None:
    world = create_world()
    factory, _module = create_pressing_factory(world, machine_count=1)
    connect_power(world, [("factory", factory.id)])

    tick(world, 10)

    assert factory.status == FactoryStatus.WORKING
    assert factory.status != FactoryStatus.UNDERPOWERED
    assert factory.get_output_amount("iron_sheet") == 2


def test_4_power_network_priority_and_underpowered_progress() -> None:
    world = create_world()
    factory, _module = create_pressing_factory(
        world,
        factory_id=1,
        module_id=1,
        machine_count=3,
        level=2,
        priority=10,
    )
    node = create_iron_node(world, node_id=1)
    producer = create_mine(
        world,
        node,
        producer_id=2,
        machine_count=2,
        priority=100,
    )
    connect_power(
        world,
        [
            ("factory", factory.id),
            ("producer", producer.id),
        ],
    )

    tick(world, 10)

    assert factory.status == FactoryStatus.WORKING
    assert factory.get_output_amount("iron_sheet") == 6
    assert producer.status == ProducerStatus.UNDERPOWERED
    assert producer.output_items == {}
    assert all(machine.progress == 0 for machine in producer.installed_machines)
    assert all(
        machine.status == MachineStatus.UNDERPOWERED
        for machine in producer.installed_machines
    )


def test_5_incompatible_machine_installation_fails() -> None:
    world = create_world()
    factory = FactoryBuilding(id=1, name="Ironworks")
    module = ModuleInstance(id=1, module_type="pressing_line")
    assert factory.add_module(module, world.definitions)

    mixer = MachineInstance(id=1, machine_type="mechanical_mixer")
    assert not can_install_machine_in_module(
        factory,
        module,
        mixer,
        world.definitions,
    )
    assert module.installed_machines == []

    node = create_iron_node(world)
    producer = ProducerBuilding(
        id=1,
        name="Iron Mine",
        producer_type="mine",
        resource_node_id=node.id,
    )
    saw = MachineInstance(id=2, machine_type="mechanical_saw")
    assert not can_install_machine_in_producer(producer, saw, world.definitions)
    assert producer.installed_machines == []


def test_6_producer_incompatible_node_invalid() -> None:
    world = create_world()
    node = create_iron_node(world)
    producer = ProducerBuilding(
        id=1,
        name="Bad Quarry",
        producer_type="quarry",
        resource_node_id=node.id,
    )
    producer.add_machine(MachineInstance(id=1, machine_type="mechanical_drill"))
    world.add_producer(producer)
    connect_power(world, [("producer", producer.id)])

    tick(world, 10)

    assert producer.status == ProducerStatus.INVALID_NODE
    assert producer.output_items == {}
    assert producer.installed_machines[0].progress == 0


def test_7_depleted_node_clamps_output_and_stops() -> None:
    world = create_world()
    node = create_iron_node(world, remaining_amount=1)
    producer = create_mine(world, node)
    connect_power(world, [("producer", producer.id)])

    tick(world, 10)

    assert producer.status == ProducerStatus.DEPLETED
    assert node.remaining_amount == 0
    assert producer.get_output_amount("raw_iron") == 1

    tick(world, 10)

    assert producer.status == ProducerStatus.DEPLETED
    assert node.remaining_amount == 0
    assert producer.get_output_amount("raw_iron") == 1


def test_8_runtime_serialization_roundtrip() -> None:
    world = create_world()
    factory, _module = create_pressing_factory(world)
    node = create_iron_node(world)
    producer = create_mine(world, node)
    connect_power(
        world,
        [
            ("factory", factory.id),
            ("producer", producer.id),
        ],
    )

    tick(world, 1)

    data = world.to_dict()
    restored = World.from_dict(data)

    assert restored.id == world.id
    assert restored.name == world.name
    assert restored.simulated_time == world.simulated_time
    assert restored.inventory == world.inventory
    assert len(restored.factories) == 1
    assert len(restored.factories[0].modules) == 1
    assert len(restored.factories[0].modules[0].installed_machines) == 2
    assert len(restored.resource_nodes) == 1
    assert len(restored.producers) == 1
    assert len(restored.producers[0].installed_machines) == 2
    assert len(restored.su_sources) == 1
    assert len(restored.power_networks) == 1
    assert "sources" in data["power_networks"][0]
    assert "source_ids" not in data["power_networks"][0]
    assert restored.power_networks[0].sources[0].source_type == "su_source"
    assert restored.power_networks[0].sources[0].source_id == 1
    assert restored.power_networks[0].consumers[0].consumer_type == "factory"
    assert "su_required" in data
    assert "su_requiered" not in data
    assert restored.factories[0].modules[0].installed_machines[0].status == MachineStatus.WORKING

    legacy_network = PowerNetwork.from_dict(
        {
            "id": 99,
            "name": "Legacy Network",
            "source_ids": [7],
            "consumers": [],
        }
    )
    assert legacy_network.sources[0].source_type == "su_source"
    assert legacy_network.sources[0].source_id == 7


TESTS = [
    ("Test 1: factory production basica", test_1_factory_production_basic),
    ("Test 2: producer/resource node basico", test_2_producer_resource_node_basic),
    ("Test 3: PowerNetwork suficiente", test_3_power_network_sufficient),
    (
        "Test 4: PowerNetwork insuficiente por prioridad",
        test_4_power_network_priority_and_underpowered_progress,
    ),
    (
        "Test 5: maquina incompatible falla claramente",
        test_5_incompatible_machine_installation_fails,
    ),
    (
        "Test 6: producer con nodo incompatible",
        test_6_producer_incompatible_node_invalid,
    ),
    (
        "Test 7: node agotado no baja de cero",
        test_7_depleted_node_clamps_output_and_stops,
    ),
    (
        "Test 8: serializacion runtime minima",
        test_8_runtime_serialization_roundtrip,
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
