from app.engine.core.world import World
from app.engine.inventory.entity_stack import EntityStack
from app.engine.inventory.inventory import Inventory
from app.engine.systems.construction import (
    add_machine_to_inventory,
    build_machine_to_inventory,
)


def test_1_default_objects_exist() -> None:
    world = World(id=1, name="Objects")

    assert world.definitions.get_object("iron_ingot").stack_kind == "normal"
    assert world.definitions.get_object("mechanical_press").entity_type == "machine"


def test_2_inventory_normal_items_compatibility() -> None:
    inventory = Inventory()
    inventory.update({"andesite_alloy": 5})
    inventory["iron_sheet"] = 2

    assert inventory.get("andesite_alloy") == 5
    assert dict(inventory) == {"andesite_alloy": 5, "iron_sheet": 2}
    assert inventory.remove_normal_item("andesite_alloy", 3)
    assert inventory["andesite_alloy"] == 2


def test_3_inventory_entity_stack_roundtrip() -> None:
    inventory = Inventory()
    inventory.add_entity_stack(
        EntityStack(
            object_id="mechanical_press",
            entity_type="machine",
            amount=2,
            entity_data={"level": 2, "metadata": {"tag": "test"}},
        )
    )

    restored = Inventory.from_dict(inventory.to_dict())

    assert len(restored.entity_items) == 1
    assert restored.entity_items[0].amount == 2
    assert restored.entity_items[0].entity_data["level"] == 2


def test_4_build_machine_to_inventory_consumes_resources() -> None:
    world = World(id=1, name="Machine Inventory")
    world.inventory.update({"andesite_alloy": 2, "iron_sheet": 1})

    assert build_machine_to_inventory(
        world.inventory,
        world.definitions,
        "mechanical_press",
        level=2,
        metadata={"line": "A"},
    )

    assert dict(world.inventory) == {}
    assert len(world.inventory.entity_items) == 1
    stack = world.inventory.entity_items[0]
    assert stack.object_id == "mechanical_press"
    assert stack.entity_data["level"] == 2
    assert stack.entity_data["metadata"]["line"] == "A"


def test_5_add_machine_to_inventory_loses_progress() -> None:
    from app.engine.entities.machine_instance import MachineInstance

    inventory = Inventory()
    machine = MachineInstance(
        id=1,
        machine_type="mechanical_press",
        level=3,
        progress=4.5,
        metadata={"line": "B"},
    )

    add_machine_to_inventory(inventory, machine)

    stack = inventory.entity_items[0]
    assert stack.entity_data["level"] == 3
    assert stack.entity_data["metadata"]["line"] == "B"
    assert "progress" not in stack.entity_data


def test_6_world_inventory_roundtrip() -> None:
    world = World(id=1, name="Inventory World")
    world.add_inventory_item("iron_ingot", 10)
    world.inventory.add_entity_stack(
        EntityStack(
            object_id="mechanical_press",
            entity_type="machine",
            amount=1,
            entity_data={"level": 1},
        )
    )

    data = world.to_dict()
    restored = World.from_dict(data)

    assert "normal_items" in data["inventory"]
    assert restored.get_inventory_amount("iron_ingot") == 10
    assert len(restored.inventory.entity_items) == 1


TESTS = [
    ("Test 1: default objects exist", test_1_default_objects_exist),
    ("Test 2: inventory normal compatibility", test_2_inventory_normal_items_compatibility),
    ("Test 3: entity stack roundtrip", test_3_inventory_entity_stack_roundtrip),
    ("Test 4: build machine to inventory", test_4_build_machine_to_inventory_consumes_resources),
    ("Test 5: add machine loses progress", test_5_add_machine_to_inventory_loses_progress),
    ("Test 6: world inventory roundtrip", test_6_world_inventory_roundtrip),
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
