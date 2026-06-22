import json
from pathlib import Path

from app.engine.content.loader import (
    DefinitionLoadError,
    load_game_definitions_from_path,
    load_game_definitions_from_template,
)
from app.engine.definitions.game_definitions import create_default_definitions


DEFAULT_TEMPLATE_PATH = Path(__file__).parent / "templates" / "default"


TEMPLATE_FILES = [
    "machines.json",
    "objects.json",
    "modules.json",
    "recipes.json",
    "su_units.json",
    "su_producers.json",
    "factory_levels.json",
    "resource_nodes.json",
    "producers.json",
]


def copy_template(source: Path, target: Path) -> None:
    target.mkdir()
    for file_name in TEMPLATE_FILES:
        (target / file_name).write_text(
            (source / file_name).read_text(encoding="utf-8"),
            encoding="utf-8",
        )


def test_1_load_default_template() -> None:
    definitions = load_game_definitions_from_template("default")

    assert definitions.get_machine("mechanical_press") is not None
    assert definitions.get_object("iron_ingot").stack_kind == "normal"
    assert definitions.get_object("raw_iron").category == "resource"
    assert definitions.get_object("iron_ingot").category == "material"
    assert definitions.get_object("iron_sheet").category == "sheet"
    assert definitions.get_object("shaft").category == "kinetic_component"
    assert definitions.get_object("andesite_casing").category == "casing"
    assert definitions.get_object("precision_mechanism").category == "advanced_component"
    assert definitions.get_object("coal").category == "fuel"
    assert definitions.get_object("water").category == "fluid"
    assert definitions.get_object("iron_plate") is None
    assert definitions.get_object("copper_plate") is None
    assert definitions.get_object("gold_ingot").category == "material"
    assert definitions.get_object("mechanical_press").entity_type == "machine"
    assert definitions.get_module("pressing_line") is not None
    assert definitions.get_recipe("press_iron_sheet") is not None
    assert definitions.get_recipe("press_iron_plate") is None
    assert definitions.get_recipe("press_copper_plate") is None
    assert definitions.get_recipe("press_gold_sheet").input_items == {"gold_ingot": 1}
    assert definitions.get_recipe("press_sturdy_sheet").output_items == {"sturdy_sheet": 1}
    assert definitions.get_su_unit("water_wheel_unit") is not None
    assert definitions.get_su_producer("river_power_complex") is not None
    assert definitions.get_factory_level(1) is not None
    assert definitions.get_resource_node_definition("iron_deposit") is not None
    assert (
        definitions.get_resource_node_definition("andesite_outcrop").resource_type
        == "andesite"
    )
    assert (
        definitions.get_resource_node_definition("redstone_deposit").resource_type
        == "redstone"
    )
    assert definitions.get_producer("mine") is not None
    assert definitions.get_producer("mine").allowed_machine_types == [
        "mechanical_drill"
    ]
    assert "redstone_deposit" in definitions.get_producer("mine").allowed_node_types
    assert "andesite_outcrop" in definitions.get_producer("quarry").allowed_node_types
    assert definitions.get_producer("mine").get_level_definition(1).machine_slots == 2
    assert definitions.get_object("mine").entity_type == "producer"
    assert definitions.get_object("mine").metadata["factory_lab_abstraction"] is True
    assert definitions.get_object("river_power_complex").entity_type == "su_producer"
    assert (
        definitions.get_object("river_power_complex").metadata["building_role"]
        == "power_generation"
    )
    assert definitions.get_object("water_wheel_unit").entity_type == "su_unit"
    assert definitions.get_object("steam_engine_unit").entity_type == "su_unit"
    assert definitions.get_su_unit("steam_engine_unit").input_items == {"coal": 1}

    for machine_id in definitions.machines:
        assert definitions.get_object(machine_id).entity_type == "machine"
    for producer_id in definitions.producers:
        assert definitions.get_object(producer_id).entity_type == "producer"
    for su_producer_id in definitions.su_producers:
        assert definitions.get_object(su_producer_id).entity_type == "su_producer"
    for su_unit_id in definitions.su_units:
        assert definitions.get_object(su_unit_id).entity_type == "su_unit"


def test_2_create_default_definitions_uses_template_loader() -> None:
    definitions = create_default_definitions()

    assert definitions.get_machine("mechanical_press").build_cost == {
        "andesite_alloy": 2,
        "iron_sheet": 1,
    }
    assert definitions.get_object("raw_iron").category == "resource"
    assert definitions.get_producer("mine").get_level_definition(2).upgrade_cost == {
        "andesite_alloy": 8,
        "iron_sheet": 6,
        "shaft": 4,
    }
    assert definitions.get_su_producer(
        "river_power_complex"
    ).get_level_definition(1).unit_slots == 6


def test_3_invalid_recipe_machine_reference_fails(tmp_path: Path) -> None:
    source = DEFAULT_TEMPLATE_PATH
    target = tmp_path / "bad_template"
    copy_template(source, target)

    recipes_path = target / "recipes.json"
    recipes = json.loads(recipes_path.read_text(encoding="utf-8"))
    recipes["press_iron_sheet"]["required_machines"] = ["missing_machine"]
    recipes_path.write_text(json.dumps(recipes), encoding="utf-8")

    try:
        load_game_definitions_from_path(target)
    except DefinitionLoadError as exc:
        assert "requires unknown machine missing_machine" in str(exc)
    else:
        raise AssertionError("Expected DefinitionLoadError")


def test_4_invalid_recipe_item_reference_fails(tmp_path: Path) -> None:
    source = DEFAULT_TEMPLATE_PATH
    target = tmp_path / "bad_recipe_item_template"
    copy_template(source, target)

    recipes_path = target / "recipes.json"
    recipes = json.loads(recipes_path.read_text(encoding="utf-8"))
    recipes["press_iron_sheet"]["input_items"] = {"missing_item": 1}
    recipes_path.write_text(json.dumps(recipes), encoding="utf-8")

    try:
        load_game_definitions_from_path(target)
    except DefinitionLoadError as exc:
        assert "uses unknown object missing_item" in str(exc)
    else:
        raise AssertionError("Expected DefinitionLoadError")


def test_5_invalid_entity_object_reference_fails(tmp_path: Path) -> None:
    source = DEFAULT_TEMPLATE_PATH
    target = tmp_path / "bad_object_template"
    copy_template(source, target)

    machines_path = target / "machines.json"
    machines = json.loads(machines_path.read_text(encoding="utf-8"))
    machines.pop("mechanical_press")
    machines_path.write_text(json.dumps(machines), encoding="utf-8")

    try:
        load_game_definitions_from_path(target)
    except DefinitionLoadError as exc:
        assert "entity_type machine but no MachineDefinition exists" in str(exc)
    else:
        raise AssertionError("Expected DefinitionLoadError")


def test_6_invalid_resource_node_output_fails(tmp_path: Path) -> None:
    source = DEFAULT_TEMPLATE_PATH
    target = tmp_path / "bad_resource_template"
    copy_template(source, target)

    nodes_path = target / "resource_nodes.json"
    nodes = json.loads(nodes_path.read_text(encoding="utf-8"))
    nodes["iron_deposit"]["resource_type"] = "missing_item"
    nodes_path.write_text(json.dumps(nodes), encoding="utf-8")

    try:
        load_game_definitions_from_path(target)
    except DefinitionLoadError as exc:
        assert "uses unknown object missing_item" in str(exc)
    else:
        raise AssertionError("Expected DefinitionLoadError")


def test_7_missing_object_definition_for_definition_fails(tmp_path: Path) -> None:
    cases = [
        ("objects_missing_machine", "mechanical_press", "MachineDefinition"),
        ("objects_missing_producer", "mine", "ProducerDefinition"),
        ("objects_missing_su_producer", "river_power_complex", "SUProducerDefinition"),
        ("objects_missing_su_unit", "water_wheel_unit", "SUUnitDefinition"),
    ]

    for folder_name, object_id, label in cases:
        target = tmp_path / folder_name
        copy_template(DEFAULT_TEMPLATE_PATH, target)
        objects_path = target / "objects.json"
        objects = json.loads(objects_path.read_text(encoding="utf-8"))
        objects.pop(object_id)
        objects_path.write_text(json.dumps(objects), encoding="utf-8")

        try:
            load_game_definitions_from_path(target)
        except DefinitionLoadError as exc:
            assert f"Missing ObjectDefinition for {label} '{object_id}'" in str(exc)
        else:
            raise AssertionError("Expected DefinitionLoadError")


def test_8_wrong_entity_type_fails(tmp_path: Path) -> None:
    target = tmp_path / "wrong_entity_type"
    copy_template(DEFAULT_TEMPLATE_PATH, target)

    objects_path = target / "objects.json"
    objects = json.loads(objects_path.read_text(encoding="utf-8"))
    objects["mechanical_press"]["entity_type"] = "producer"
    objects_path.write_text(json.dumps(objects), encoding="utf-8")

    try:
        load_game_definitions_from_path(target)
    except DefinitionLoadError as exc:
        assert (
            "ObjectDefinition 'mechanical_press' has entity_type "
            "'producer' but expected 'machine'"
        ) in str(exc)
    else:
        raise AssertionError("Expected DefinitionLoadError")


def test_9_unsupported_entity_type_fails(tmp_path: Path) -> None:
    target = tmp_path / "unsupported_entity_type"
    copy_template(DEFAULT_TEMPLATE_PATH, target)

    objects_path = target / "objects.json"
    objects = json.loads(objects_path.read_text(encoding="utf-8"))
    objects["mechanical_press"]["entity_type"] = "mystery"
    objects_path.write_text(json.dumps(objects), encoding="utf-8")

    try:
        load_game_definitions_from_path(target)
    except DefinitionLoadError as exc:
        assert "Unsupported entity_type 'mystery'" in str(exc)
    else:
        raise AssertionError("Expected DefinitionLoadError")


def test_10_game_definitions_roundtrip() -> None:
    definitions = load_game_definitions_from_template("default")
    restored = type(definitions).from_dict(definitions.to_dict())

    assert restored.get_machine("mechanical_press").su_cost == 1024
    assert restored.get_object("mechanical_press").stack_kind == "entity"
    assert restored.get_module("pressing_line").allowed_machine_types == [
        "mechanical_press"
    ]
    assert restored.get_recipe("press_iron_sheet").duration == 5.0
    assert restored.get_su_unit("water_wheel_unit").su_output == 1024
    assert restored.get_object("steam_engine_unit").entity_type == "su_unit"
    assert restored.get_su_producer(
        "river_power_complex"
    ).get_level_definition(1).unit_slots == 6
    assert restored.get_factory_level(1).module_slots == 2
    assert restored.get_resource_node_definition("iron_deposit").resource_type == "raw_iron"
    assert restored.get_producer("mine").get_level_definition(1).machine_slots == 2


TESTS = [
    ("Test 1: carga template default", test_1_load_default_template),
    (
        "Test 2: create_default_definitions usa loader",
        test_2_create_default_definitions_uses_template_loader,
    ),
    ("Test 10: GameDefinitions roundtrip", test_10_game_definitions_roundtrip),
]


def main() -> int:
    import tempfile

    failures = []

    for name, test in TESTS:
        try:
            test()
        except AssertionError as exc:
            failures.append((name, str(exc)))
            print(f"FAIL - {name}")
        else:
            print(f"PASS - {name}")

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            test_3_invalid_recipe_machine_reference_fails(Path(temp_dir))
    except AssertionError as exc:
        failures.append(("Test 3: referencia invalida falla", str(exc)))
        print("FAIL - Test 3: referencia invalida falla")
    else:
        print("PASS - Test 3: referencia invalida falla")

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            test_4_invalid_recipe_item_reference_fails(Path(temp_dir))
    except AssertionError as exc:
        failures.append(("Test 4: recipe item invalido falla", str(exc)))
        print("FAIL - Test 4: recipe item invalido falla")
    else:
        print("PASS - Test 4: recipe item invalido falla")

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            test_5_invalid_entity_object_reference_fails(Path(temp_dir))
    except AssertionError as exc:
        failures.append(("Test 5: objeto entidad invalido falla", str(exc)))
        print("FAIL - Test 5: objeto entidad invalido falla")
    else:
        print("PASS - Test 5: objeto entidad invalido falla")

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            test_6_invalid_resource_node_output_fails(Path(temp_dir))
    except AssertionError as exc:
        failures.append(("Test 6: resource node output invalido falla", str(exc)))
        print("FAIL - Test 6: resource node output invalido falla")
    else:
        print("PASS - Test 6: resource node output invalido falla")

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            test_7_missing_object_definition_for_definition_fails(Path(temp_dir))
    except AssertionError as exc:
        failures.append(("Test 7: ObjectDefinition faltante falla", str(exc)))
        print("FAIL - Test 7: ObjectDefinition faltante falla")
    else:
        print("PASS - Test 7: ObjectDefinition faltante falla")

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            test_8_wrong_entity_type_fails(Path(temp_dir))
    except AssertionError as exc:
        failures.append(("Test 8: entity_type incorrecto falla", str(exc)))
        print("FAIL - Test 8: entity_type incorrecto falla")
    else:
        print("PASS - Test 8: entity_type incorrecto falla")

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            test_9_unsupported_entity_type_fails(Path(temp_dir))
    except AssertionError as exc:
        failures.append(("Test 9: entity_type no soportado falla", str(exc)))
        print("FAIL - Test 9: entity_type no soportado falla")
    else:
        print("PASS - Test 9: entity_type no soportado falla")

    total = len(TESTS) + 7
    print(f"\nResult: {total - len(failures)}/{total} tests passed")

    if failures:
        print("\nFailures:")
        for name, message in failures:
            suffix = f": {message}" if message else ""
            print(f"- {name}{suffix}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
