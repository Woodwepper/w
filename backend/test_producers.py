from fastapi.testclient import TestClient

from app.api import memory_store
from app.engine.instances.power_network import PowerNetwork
from app.engine.instances.su_source_instance import SUSourceInstance
from app.engine.models.producer_building import ProducerBuilding
from app.engine.models.producer_status import ProducerStatus
from app.engine.models.resource_node import ResourceNode
from app.engine.models.world import World
from app.engine.simulation import tick
from app.main import app


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


def test_1_api_producer_flow() -> None:
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
        for item in producer_catalog["producers"]
    )

    node = client.post(
        f"/api/worlds/{world_id}/resource-nodes",
        json={
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
        },
    ).json()

    producer = client.post(
        f"/api/worlds/{world_id}/producers",
        json={
            "producer_type": "mine",
            "name": "Iron Mine",
            "resource_node_id": node["id"],
            "machine_level": 1,
            "efficiency_level": 1,
            "priority": 10,
        },
    ).json()

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
            "consumer_id": producer["id"],
        },
    )

    state = client.post(
        f"/api/worlds/{world_id}/tick",
        json={"seconds": 10},
    ).json()

    updated_producer = state["producers"][0]
    updated_node = state["resource_nodes"][0]

    assert updated_producer["status"] == ProducerStatus.WORKING.value
    assert updated_producer["output_items"]["raw_iron"] == 4
    assert updated_node["remaining_amount"] == 996

    collected_state = client.post(
        f"/api/worlds/{world_id}/producers/{producer['id']}/collect-output",
        json={"item_id": "raw_iron", "amount": 2},
    ).json()
    collected_producer = collected_state["producers"][0]

    assert collected_state["inventory"]["raw_iron"] == 2
    assert collected_producer["output_items"]["raw_iron"] == 2


def test_2_producer_underpowered() -> None:
    client = create_client()

    world = client.post("/api/worlds", json={"name": "Underpowered"}).json()
    world_id = world["id"]
    node = client.post(
        f"/api/worlds/{world_id}/resource-nodes",
        json={
            "node_type": "iron_deposit",
            "name": "Iron Deposit",
            "x": 0,
            "y": 0,
            "remaining_amount": 1000,
        },
    ).json()
    client.post(
        f"/api/worlds/{world_id}/producers",
        json={
            "producer_type": "mine",
            "name": "Unpowered Mine",
            "resource_node_id": node["id"],
        },
    )

    state = client.post(
        f"/api/worlds/{world_id}/tick",
        json={"seconds": 10},
    ).json()
    producer = state["producers"][0]

    assert producer["status"] == ProducerStatus.UNDERPOWERED.value
    assert producer["output_items"] == {}
    assert producer["progress"] == 0


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

    world.add_resource_node(node)
    world.add_producer(producer)
    connect_producer_to_water_wheel(world, producer)

    tick(world, 10)

    assert producer.status == ProducerStatus.INVALID_NODE
    assert producer.output_items == {}


def test_4_insufficient_level() -> None:
    client = create_client()

    world = client.post("/api/worlds", json={"name": "Insufficient Level"}).json()
    world_id = world["id"]
    node = client.post(
        f"/api/worlds/{world_id}/resource-nodes",
        json={
            "node_type": "iron_deposit",
            "name": "Deep Iron Deposit",
            "x": 0,
            "y": 0,
            "required_machine_level": 2,
            "remaining_amount": 1000,
        },
    ).json()
    producer = client.post(
        f"/api/worlds/{world_id}/producers",
        json={
            "producer_type": "mine",
            "name": "Weak Mine",
            "resource_node_id": node["id"],
            "machine_level": 1,
            "efficiency_level": 1,
        },
    ).json()
    source = client.post(
        f"/api/worlds/{world_id}/su-sources",
        json={"source_type": "water_wheel", "name": "Water Wheel"},
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
            "consumer_id": producer["id"],
        },
    )

    state = client.post(
        f"/api/worlds/{world_id}/tick",
        json={"seconds": 10},
    ).json()

    assert state["producers"][0]["status"] == ProducerStatus.INSUFFICIENT_LEVEL.value
    assert state["producers"][0]["output_items"] == {}


def test_5_api_rejects_incompatible_producer_node() -> None:
    client = create_client()

    world = client.post("/api/worlds", json={"name": "API Validation"}).json()
    world_id = world["id"]
    node = client.post(
        f"/api/worlds/{world_id}/resource-nodes",
        json={
            "node_type": "iron_deposit",
            "name": "Iron Deposit",
            "x": 0,
            "y": 0,
            "remaining_amount": 1000,
        },
    ).json()

    response = client.post(
        f"/api/worlds/{world_id}/producers",
        json={
            "producer_type": "quarry",
            "name": "Rejected Quarry",
            "resource_node_id": node["id"],
        },
    )

    assert response.status_code == 400


TESTS = [
    ("Test 1: API producer flow", test_1_api_producer_flow),
    ("Test 2: producer underpowered", test_2_producer_underpowered),
    ("Test 3: invalid node engine state", test_3_invalid_node_engine_state),
    ("Test 4: insufficient level", test_4_insufficient_level),
    ("Test 5: API rejects incompatible producer node", test_5_api_rejects_incompatible_producer_node),
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
