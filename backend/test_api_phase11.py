from fastapi.testclient import TestClient

from app.api import memory_store
from app.main import app


def reset_memory_store() -> None:
    memory_store.worlds.clear()
    memory_store.next_world_id = 1
    memory_store.next_factory_id = 1
    memory_store.next_module_id = 1
    memory_store.next_machine_id = 1
    memory_store.next_su_producer_id = 1
    memory_store.next_power_network_id = 1
    memory_store.next_resource_node_id = 1
    memory_store.next_producer_id = 1


def create_client() -> TestClient:
    reset_memory_store()
    return TestClient(app)


def add_inventory(client: TestClient, world_id: int, items: dict[str, int]) -> None:
    for item_id, amount in items.items():
        response = client.post(
            f"/api/worlds/{world_id}/inventory/test-add",
            json={"item_id": item_id, "amount": amount},
        )
        assert response.status_code == 200


def create_world_surface(client: TestClient) -> dict:
    world = client.post("/api/worlds", json={"name": "Frontend Surface"}).json()
    world_id = world["id"]
    add_inventory(
        client,
        world_id,
        {
            "andesite_alloy": 10,
            "shaft": 4,
            "iron_sheet": 10,
            "iron_ingot": 10,
        },
    )

    factory = client.post(
        f"/api/worlds/{world_id}/factories",
        json={"name": "Ironworks", "x": 2, "y": 3},
    ).json()
    module_factory = client.post(
        f"/api/worlds/{world_id}/factories/{factory['id']}/modules",
        json={
            "module_type": "pressing_line",
            "active_recipe": "press_iron_sheet",
        },
    ).json()
    module_id = module_factory["modules"][0]["id"]
    client.post(
        f"/api/worlds/{world_id}/factories/{factory['id']}/modules/{module_id}/machines/build-install",
        json={"machine_type": "mechanical_press"},
    )

    node = client.post(
        f"/api/worlds/{world_id}/resource-nodes",
        json={
            "node_type": "iron_deposit",
            "name": "Iron Deposit",
            "x": 4,
            "y": 4,
            "remaining_amount": 1000,
        },
    ).json()
    producer = client.post(
        f"/api/worlds/{world_id}/producers",
        json={
            "producer_type": "mine",
            "name": "Iron Mine",
            "resource_node_id": node["id"],
            "priority": 20,
        },
    ).json()

    su_producer = client.post(
        f"/api/worlds/{world_id}/su-producers",
        json={
            "producer_type": "river_power_complex",
            "name": "River Power",
            "x": 0,
            "y": 0,
        },
    ).json()
    client.post(
        f"/api/worlds/{world_id}/su-producers/{su_producer['id']}/units",
        json={"unit_type": "water_wheel_unit", "amount": 2},
    )

    network = client.post(
        f"/api/worlds/{world_id}/power-networks",
        json={"name": "Main Grid"},
    ).json()
    client.post(
        f"/api/worlds/{world_id}/power-networks/{network['id']}/sources",
        json={
            "su_producer_id": su_producer["id"],
        },
    )
    client.post(
        f"/api/worlds/{world_id}/power-networks/{network['id']}/consumers",
        json={
            "consumer_type": "factory",
            "consumer_id": factory["id"],
        },
    )

    return {
        "world_id": world_id,
        "factory_id": factory["id"],
        "producer_id": producer["id"],
        "su_producer_id": su_producer["id"],
        "network_id": network["id"],
    }


def test_1_world_overview_and_map() -> None:
    client = create_client()
    ids = create_world_surface(client)

    overview = client.get(f"/api/worlds/{ids['world_id']}/overview").json()
    world_map = client.get(f"/api/worlds/{ids['world_id']}/map").json()

    assert overview["counts"]["factories"] == 1
    assert overview["counts"]["su_producers"] == 1
    assert "inventory" in overview
    assert any(node["kind"] == "factory" for node in world_map["nodes"])
    assert any(node["kind"] == "resource_node" for node in world_map["nodes"])
    assert len(world_map["power_networks"]) == 1


def test_2_detail_endpoints_resolve_definitions() -> None:
    client = create_client()
    ids = create_world_surface(client)

    factory_detail = client.get(
        f"/api/worlds/{ids['world_id']}/factories/{ids['factory_id']}/detail"
    ).json()
    producer_detail = client.get(
        f"/api/worlds/{ids['world_id']}/producers/{ids['producer_id']}/detail"
    ).json()
    su_producer_detail = client.get(
        f"/api/worlds/{ids['world_id']}/su-producers/{ids['su_producer_id']}/detail"
    ).json()
    network_detail = client.get(
        f"/api/worlds/{ids['world_id']}/power-networks/{ids['network_id']}/detail"
    ).json()

    assert factory_detail["module_details"][0]["definition"]["id"] == "pressing_line"
    assert factory_detail["module_details"][0]["machine_details"][0]["definition"]["id"] == "mechanical_press"
    assert producer_detail["definition"]["id"] == "mine"
    assert producer_detail["resource_node"]["node_type"] == "iron_deposit"
    assert su_producer_detail["unit_details"][0]["definition"]["id"] == "water_wheel_unit"
    assert network_detail["resolved_sources"][0]["entity"]["producer_type"] == "river_power_complex"
    assert network_detail["resolved_consumers"][0]["entity"]["name"] == "Ironworks"


TESTS = [
    ("Test 1: world overview and map", test_1_world_overview_and_map),
    ("Test 2: detail endpoints resolve definitions", test_2_detail_endpoints_resolve_definitions),
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
