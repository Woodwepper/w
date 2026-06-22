from fastapi.testclient import TestClient

from app.api import memory_store
from app.engine.instances.machine_instance import MachineInstance
from app.engine.instances.power_network import PowerNetwork
from app.engine.instances.su_source_instance import SUSourceInstance
from app.engine.models.producer_building import ProducerBuilding
from app.engine.models.producer_status import ProducerStatus
from app.engine.models.resource_node import ResourceNode
from app.engine.models.world import World
from app.engine.power import calculate_producer_su_required
from app.engine.simulation import tick
from app.main import app


DRILL_BUILD_COST = {
    "andesite_alloy": 3,
    "iron_sheet": 2,
    "shaft": 1,
}


def reset_memory_store() -> None:
    memory_store.worlds.clear()
    memory_store.next_world_id = 1
    memory_store.next_factory_id = 1
    memory_store.next_module_id = 1
    memory_store.next_machine_id = 1
    memory_store.next_su_source_id = 1
    memory_store.next_power_network_id = 1
    memory_store.next_resource_node_id = 1
    memory_store.next_producer_id = 1


def create_client() -> TestClient:
    reset_memory_store()
    return TestClient(app)


def seed_drill_resources(client: TestClient, world_id: int, multiplier: int = 1) -> None:
    for item_id, amount in DRILL_BUILD_COST.items():
        client.post(
            f"/api/worlds/{world_id}/inventory/test-add",
            json={
                "item_id": item_id,
                "amount": amount * multiplier,
            },
        )


def create_iron_node(client: TestClient, world_id: int, **overrides) -> dict:
    payload = {
        "node_type": "iron_deposit",
        "name": "Iron Deposit",
        "x": 4,
        "y": 2,
        "richness": 1,
        "hardness": 1.0,
        "required_machine_level": 1,
        "remaining_amount": 1000,
        "infinite": False,
        "traits": [],
    }
    payload.update(overrides)
    return client.post(
        f"/api/worlds/{world_id}/resource-nodes",
        json=payload,
    ).json()


def create_mine(client: TestClient, world_id: int, node_id: int, **overrides) -> dict:
    payload = {
        "producer_type": "mine",
        "name": "Iron Mine",
        "resource_node_id": node_id,
        "level": 1,
        "priority": 10,
    }
    payload.update(overrides)
    return client.post(
        f"/api/worlds/{world_id}/producers",
        json=payload,
    ).json()


def build_drill(client: TestClient, world_id: int, producer_id: int, level: int = 1):
    return client.post(
        f"/api/worlds/{world_id}/producers/{producer_id}/machines/build-install",
        json={
            "machine_type": "mechanical_drill",
            "level": level,
            "metadata": {},
        },
    )


def connect_producer_power(client: TestClient, world_id: int, producer_id: int) -> None:
    source = client.post(
        f"/api/worlds/{world_id}/su-sources",
        json={
            "source_type": "water_wheel",
            "name": "Water Wheel",
            "x": 0,
            "y": 0,
        },
    ).json()
    network = client.post(
        f"/api/worlds/{world_id}/power-networks",
        json={"name": "Main Grid"},
    ).json()
    client.post(
        f"/api/worlds/{world_id}/power-networks/{network['id']}/sources",
        json={"source_id": source["id"]},
    )
    client.post(
        f"/api/worlds/{world_id}/power-networks/{network['id']}/consumers",
        json={
            "consumer_type": "producer",
            "consumer_id": producer_id,
        },
    )


def connect_producer_to_water_wheel(
    world: World,
    producer: ProducerBuilding,
) -> None:
    world.add_su_source(
        SUSourceInstance(
            id=1,
            source_type="water_wheel",
            name="Water Wheel",
        )
    )
    network = PowerNetwork(id=1, name="Main Grid")
    network.add_source(1)
    network.add_consumer("producer", producer.id)
    world.add_power_network(network)


def test_1_api_producer_flow_with_real_machines() -> None:
    client = create_client()

    world = client.post("/api/worlds", json={"name": "Producer World"}).json()
    world_id = world["id"]

    resource_catalog = client.get(
        f"/api/worlds/{world_id}/catalog/resource-nodes"
    ).json()
    producer_catalog = client.get(
        f"/api/worlds/{world_id}/catalog/producers"
    ).json()

    assert any(
        item["id"] == "iron_deposit"
        for item in resource_catalog["resource_nodes"]
    )
    assert any(
        item["id"] == "mine"
        and "mechanical_drill" in item["allowed_machine_types"]
        for item in producer_catalog["producers"]
    )

    node = create_iron_node(client, world_id)
    producer = create_mine(client, world_id, node["id"])

    seed_drill_resources(client, world_id, multiplier=2)
    first_response = build_drill(client, world_id, producer["id"])
    second_response = build_drill(client, world_id, producer["id"])
    assert first_response.status_code == 200
    assert second_response.status_code == 200

    connect_producer_power(client, world_id, producer["id"])

    state = client.post(
        f"/api/worlds/{world_id}/tick",
        json={"seconds": 10},
    ).json()

    updated_producer = state["producers"][0]
    updated_node = state["resource_nodes"][0]
    machines = updated_producer["installed_machines"]

    assert updated_producer["status"] == ProducerStatus.WORKING.value
    assert updated_producer["output_items"]["raw_iron"] == 4
    assert updated_node["remaining_amount"] == 996
    assert len(machines) == 2
    assert all(machine["progress"] == 0 for machine in machines)
    assert all(machine["status"] == "working" for machine in machines)

    collected_state = client.post(
        f"/api/worlds/{world_id}/producers/{producer['id']}/collect-output",
        json={"item_id": "raw_iron", "amount": 2},
    ).json()
    collected_producer = collected_state["producers"][0]

    assert collected_state["inventory"]["raw_iron"] == 2
    assert collected_producer["output_items"]["raw_iron"] == 2


def test_2_producer_underpowered_does_not_advance_machines() -> None:
    client = create_client()

    world = client.post("/api/worlds", json={"name": "Underpowered"}).json()
    world_id = world["id"]
    node = create_iron_node(client, world_id)
    producer = create_mine(client, world_id, node["id"])

    seed_drill_resources(client, world_id)
    response = build_drill(client, world_id, producer["id"])
    assert response.status_code == 200

    state = client.post(
        f"/api/worlds/{world_id}/tick",
        json={"seconds": 10},
    ).json()
    producer_state = state["producers"][0]
    machine = producer_state["installed_machines"][0]

    assert producer_state["status"] == ProducerStatus.UNDERPOWERED.value
    assert producer_state["output_items"] == {}
    assert machine["status"] == "underpowered"
    assert machine["progress"] == 0


def test_3_invalid_node_engine_state() -> None:
    world = World(id=1, name="Invalid Node")
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
        name="Bad Quarry",
        producer_type="quarry",
        resource_node_id=node.id,
    )
    producer.add_machine(
        MachineInstance(
            id=1,
            machine_type="mechanical_drill",
        )
    )

    world.add_resource_node(node)
    world.add_producer(producer)
    connect_producer_to_water_wheel(world, producer)

    tick(world, 10)

    assert producer.status == ProducerStatus.INVALID_NODE
    assert producer.output_items == {}
    assert producer.installed_machines[0].progress == 0


def test_4_insufficient_machine_level() -> None:
    client = create_client()

    world = client.post("/api/worlds", json={"name": "Insufficient Level"}).json()
    world_id = world["id"]
    node = create_iron_node(
        client,
        world_id,
        name="Deep Iron Deposit",
        required_machine_level=2,
    )
    producer = create_mine(client, world_id, node["id"])
    seed_drill_resources(client, world_id)
    response = build_drill(client, world_id, producer["id"], level=1)
    assert response.status_code == 200
    connect_producer_power(client, world_id, producer["id"])

    state = client.post(
        f"/api/worlds/{world_id}/tick",
        json={"seconds": 10},
    ).json()

    producer_state = state["producers"][0]
    assert producer_state["status"] == ProducerStatus.INSUFFICIENT_LEVEL.value
    assert producer_state["output_items"] == {}
    assert producer_state["installed_machines"][0]["progress"] == 0


def test_5_api_rejects_incompatible_producer_node() -> None:
    client = create_client()

    world = client.post("/api/worlds", json={"name": "API Validation"}).json()
    world_id = world["id"]
    node = create_iron_node(client, world_id)

    response = client.post(
        f"/api/worlds/{world_id}/producers",
        json={
            "producer_type": "quarry",
            "name": "Rejected Quarry",
            "resource_node_id": node["id"],
        },
    )

    assert response.status_code == 400


def test_6_api_rejects_machine_not_allowed_in_producer() -> None:
    client = create_client()

    world = client.post("/api/worlds", json={"name": "Machine Validation"}).json()
    world_id = world["id"]
    node = create_iron_node(client, world_id)
    producer = create_mine(client, world_id, node["id"])

    client.post(
        f"/api/worlds/{world_id}/inventory/test-add",
        json={"item_id": "andesite_alloy", "amount": 10},
    )
    client.post(
        f"/api/worlds/{world_id}/inventory/test-add",
        json={"item_id": "iron_sheet", "amount": 10},
    )
    response = client.post(
        f"/api/worlds/{world_id}/producers/{producer['id']}/machines/build-install",
        json={
            "machine_type": "mechanical_press",
            "level": 1,
            "metadata": {},
        },
    )

    assert response.status_code == 400


def test_7_machine_slot_limit_and_level_up() -> None:
    client = create_client()

    world = client.post("/api/worlds", json={"name": "Producer Level Up"}).json()
    world_id = world["id"]
    node = create_iron_node(client, world_id)
    producer = create_mine(client, world_id, node["id"])

    seed_drill_resources(client, world_id, multiplier=3)
    assert build_drill(client, world_id, producer["id"]).status_code == 200
    assert build_drill(client, world_id, producer["id"]).status_code == 200
    assert build_drill(client, world_id, producer["id"]).status_code == 400

    inventory_seed = {
        "andesite_alloy": 8,
        "iron_sheet": 6,
        "shaft": 4,
    }
    for item_id, amount in inventory_seed.items():
        client.post(
            f"/api/worlds/{world_id}/inventory/test-add",
            json={"item_id": item_id, "amount": amount},
        )

    leveled_state = client.post(
        f"/api/worlds/{world_id}/producers/{producer['id']}/level-up"
    ).json()
    leveled_producer = leveled_state["producers"][0]

    assert leveled_producer["level"] == 2
    assert leveled_state["inventory"].get("shaft", 0) == 1
    assert build_drill(client, world_id, producer["id"]).status_code == 200


def test_8_producer_su_uses_installed_machine_costs_only() -> None:
    world = World(id=1, name="Producer SU")
    node = ResourceNode(
        id=1,
        node_type="iron_deposit",
        name="Iron Deposit",
        x=0,
        y=0,
    )
    producer = ProducerBuilding(
        id=1,
        name="Iron Mine",
        producer_type="mine",
        resource_node_id=node.id,
    )
    producer.add_machine(
        MachineInstance(
            id=1,
            machine_type="mechanical_drill",
            level=1,
        )
    )
    producer.add_machine(
        MachineInstance(
            id=2,
            machine_type="mechanical_drill",
            level=3,
        )
    )
    world.add_resource_node(node)
    world.add_producer(producer)

    assert calculate_producer_su_required(world, producer) == 2048


def test_9_upgrade_producer_machine_keeps_su_cost() -> None:
    client = create_client()

    world = client.post("/api/worlds", json={"name": "Producer Machine Upgrade"}).json()
    world_id = world["id"]
    node = create_iron_node(client, world_id)
    producer = create_mine(client, world_id, node["id"])
    seed_drill_resources(client, world_id)
    producer_with_machine = build_drill(client, world_id, producer["id"]).json()
    machine = producer_with_machine["installed_machines"][0]

    upgrade_cost = {
        "andesite_alloy": 5,
        "iron_sheet": 3,
    }
    for item_id, amount in upgrade_cost.items():
        client.post(
            f"/api/worlds/{world_id}/inventory/test-add",
            json={"item_id": item_id, "amount": amount},
        )

    upgraded_producer = client.patch(
        (
            f"/api/worlds/{world_id}/producers/{producer['id']}"
            f"/machines/{machine['id']}/upgrade"
        ),
        json={"target_level": 2},
    ).json()

    assert upgraded_producer["installed_machines"][0]["level"] == 2

    state = client.get(f"/api/worlds/{world_id}").json()
    producer_state = state["producers"][0]
    world_obj = memory_store.get_world_or_404(world_id)
    producer_obj = world_obj.get_producer(producer_state["id"])

    assert calculate_producer_su_required(world_obj, producer_obj) == 1024


TESTS = [
    ("Test 1: API producer flow with real machines", test_1_api_producer_flow_with_real_machines),
    ("Test 2: producer underpowered", test_2_producer_underpowered_does_not_advance_machines),
    ("Test 3: invalid node engine state", test_3_invalid_node_engine_state),
    ("Test 4: insufficient machine level", test_4_insufficient_machine_level),
    ("Test 5: API rejects incompatible producer node", test_5_api_rejects_incompatible_producer_node),
    ("Test 6: API rejects machine not allowed", test_6_api_rejects_machine_not_allowed_in_producer),
    ("Test 7: machine slot limit and level-up", test_7_machine_slot_limit_and_level_up),
    ("Test 8: producer SU uses installed machines", test_8_producer_su_uses_installed_machine_costs_only),
    ("Test 9: upgrade producer machine keeps SU cost", test_9_upgrade_producer_machine_keeps_su_cost),
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
