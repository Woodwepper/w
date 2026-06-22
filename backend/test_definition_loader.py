import json
from pathlib import Path

from app.engine.content.loader import (
    DefinitionLoadError,
    load_game_definitions_from_path,
    load_game_definitions_from_template,
)
from app.engine.definitions.game_definitions import create_default_definitions


TEMPLATE_FILES = [
    "machines.json",
    "modules.json",
    "recipes.json",
    "su_sources.json",
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
    assert definitions.get_module("pressing_line") is not None
    assert definitions.get_recipe("press_iron_sheet") is not None
    assert definitions.get_su_source("water_wheel") is not None
    assert definitions.get_factory_level(1) is not None
    assert definitions.get_resource_node_definition("iron_deposit") is not None
    assert definitions.get_producer("mine") is not None
    assert definitions.get_producer("mine").allowed_machine_types == [
        "mechanical_drill"
    ]
    assert definitions.get_producer("mine").get_level_definition(1).machine_slots == 2


def test_2_create_default_definitions_uses_template_loader() -> None:
    definitions = create_default_definitions()

    assert definitions.get_machine("mechanical_press").build_cost == {
        "andesite_alloy": 2,
        "iron_sheet": 1,
    }
    assert definitions.get_producer("mine").get_level_definition(2).upgrade_cost == {
        "andesite_alloy": 8,
        "iron_sheet": 6,
        "shaft": 4,
    }


def test_3_invalid_recipe_machine_reference_fails(tmp_path: Path) -> None:
    source = Path("templates/default")
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


TESTS = [
    ("Test 1: carga template default", test_1_load_default_template),
    (
        "Test 2: create_default_definitions usa loader",
        test_2_create_default_definitions_uses_template_loader,
    ),
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

    print(f"\nResult: {3 - len(failures)}/3 tests passed")

    if failures:
        print("\nFailures:")
        for name, message in failures:
            suffix = f": {message}" if message else ""
            print(f"- {name}{suffix}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
