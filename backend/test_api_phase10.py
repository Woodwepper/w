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


def test_1_catalog_exposes_new_definitions() -> None:
    client = create_client()
    world = client.post("/api/worlds", json={"name": "API Phase 10"}).json()
    world_id = world["id"]

    objects = client.get(f"/api/worlds/{world_id}/catalog/objects").json()
    su_units = client.get(f"/api/worlds/{world_id}/catalog/su-units").json()
    su_producers = client.get(
        f"/api/worlds/{world_id}/catalog/su-producers"
    ).json()

    assert any(item["id"] == "iron_ingot" for item in objects["objects"])
    assert any(item["id"] == "water_wheel_unit" for item in su_units["su_units"])
    assert any(
        item["id"] == "river_power_complex"
        for item in su_producers["su_producers"]
    )


def test_2_build_machine_into_inventory() -> None:
    client = create_client()
    world = client.post("/api/worlds", json={"name": "Inventory API"}).json()
    world_id = world["id"]
    add_inventory(client, world_id, {"andesite_alloy": 2, "iron_sheet": 1})

    response = client.post(
        f"/api/worlds/{world_id}/inventory/machines/build",
        json={
            "machine_type": "mechanical_press",
            "level": 2,
            "metadata": {"line": "A"},
        },
    )

    assert response.status_code == 200
    inventory = response.json()["inventory"]
    assert inventory["normal_items"] == {}
    assert inventory["entity_items"][0]["object_id"] == "mechanical_press"
    assert inventory["entity_items"][0]["entity_data"]["level"] == 2


def test_3_su_producer_powers_factory_by_api() -> None:
    client = create_client()
    world = client.post("/api/worlds", json={"name": "Power API"}).json()
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
        json={"name": "Ironworks"},
    ).json()
    module_factory = client.post(
        f"/api/worlds/{world_id}/factories/{factory['id']}/modules",
        json={
            "module_type": "pressing_line",
            "active_recipe": "press_iron_sheet",
        },
    ).json()
    module_id = module_factory["modules"][0]["id"]
    response = client.post(
        f"/api/worlds/{world_id}/factories/{factory['id']}/modules/{module_id}/machines/build-install",
        json={"machine_type": "mechanical_press"},
    )
    assert response.status_code == 200

    client.post(
        f"/api/worlds/{world_id}/factories/{factory['id']}/inputs",
        json={"item_id": "iron_ingot", "amount": 10},
    )

    su_producer = client.post(
        f"/api/worlds/{world_id}/su-producers",
        json={
            "producer_type": "river_power_complex",
            "name": "River Power",
        },
    ).json()
    response = client.post(
        f"/api/worlds/{world_id}/su-producers/{su_producer['id']}/units",
        json={"unit_type": "water_wheel_unit", "amount": 2},
    )
    assert response.status_code == 200

    network = client.post(
        f"/api/worlds/{world_id}/power-networks",
        json={"name": "Grid"},
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

    state = client.post(
        f"/api/worlds/{world_id}/tick",
        json={"seconds": 10},
    ).json()

    updated_factory = state["factories"][0]
    assert updated_factory["output_items"]["iron_sheet"] == 2
    assert state["su_producers"][0]["status"] == "active"


TESTS = [
    ("Test 1: catalogs expose new definitions", test_1_catalog_exposes_new_definitions),
    ("Test 2: build machine into inventory", test_2_build_machine_into_inventory),
    ("Test 3: SUProducer powers factory by API", test_3_su_producer_powers_factory_by_api),
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
