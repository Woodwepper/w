import json
from pathlib import Path
from typing import Any

from app.engine.definitions.factory_level_definition import FactoryLevelDefinition
from app.engine.definitions.machine_definition import MachineDefinition
from app.engine.definitions.module_definition import ModuleDefinition
from app.engine.definitions.producer_definition import ProducerDefinition
from app.engine.definitions.recipe_definition import Recipe
from app.engine.definitions.resource_node_definition import ResourceNodeDefinition
from app.engine.definitions.su_source_definition import SUSourceDefinition


class DefinitionLoadError(ValueError):
    pass


REQUIRED_TEMPLATE_FILES = {
    "machines": "machines.json",
    "modules": "modules.json",
    "recipes": "recipes.json",
    "su_sources": "su_sources.json",
    "factory_levels": "factory_levels.json",
    "resource_nodes": "resource_nodes.json",
    "producers": "producers.json",
}


def load_game_definitions_from_template(template_name: str):
    template_path = _templates_root() / template_name
    return load_game_definitions_from_path(template_path)


def load_game_definitions_from_path(path: str | Path):
    from app.engine.definitions.game_definitions import GameDefinitions

    template_path = Path(path)
    raw_data = {
        key: _load_json_object(template_path / file_name)
        for key, file_name in REQUIRED_TEMPLATE_FILES.items()
    }

    definitions = GameDefinitions(
        machines={
            machine_id: MachineDefinition.from_dict(data)
            for machine_id, data in raw_data["machines"].items()
        },
        modules={
            module_id: ModuleDefinition.from_dict(data)
            for module_id, data in raw_data["modules"].items()
        },
        recipes={
            recipe_id: Recipe.from_dict(data)
            for recipe_id, data in raw_data["recipes"].items()
        },
        su_sources={
            source_id: SUSourceDefinition.from_dict(data)
            for source_id, data in raw_data["su_sources"].items()
        },
        factory_levels={
            int(level): FactoryLevelDefinition.from_dict(data)
            for level, data in raw_data["factory_levels"].items()
        },
        resource_nodes={
            node_id: ResourceNodeDefinition.from_dict(data)
            for node_id, data in raw_data["resource_nodes"].items()
        },
        producers={
            producer_id: ProducerDefinition.from_dict(data)
            for producer_id, data in raw_data["producers"].items()
        },
    )

    validate_game_definitions(definitions)
    return definitions


def validate_game_definitions(definitions) -> None:
    _validate_mapping_ids("machine", definitions.machines)
    _validate_mapping_ids("module", definitions.modules)
    _validate_mapping_ids("recipe", definitions.recipes)
    _validate_mapping_ids("su_source", definitions.su_sources)
    _validate_mapping_ids("resource_node", definitions.resource_nodes)
    _validate_mapping_ids("producer", definitions.producers)
    _validate_factory_levels(definitions.factory_levels)

    for recipe in definitions.recipes.values():
        for machine_id in recipe.required_machines:
            _require_key(
                definitions.machines,
                machine_id,
                f"Recipe {recipe.id} requires unknown machine {machine_id}",
            )

    for machine in definitions.machines.values():
        for recipe_id in machine.allowed_recipes:
            _require_key(
                definitions.recipes,
                recipe_id,
                f"Machine {machine.id} allows unknown recipe {recipe_id}",
            )

    for module in definitions.modules.values():
        for recipe_id in module.allowed_recipes:
            _require_key(
                definitions.recipes,
                recipe_id,
                f"Module {module.id} allows unknown recipe {recipe_id}",
            )
        for machine_id in module.allowed_machine_types:
            _require_key(
                definitions.machines,
                machine_id,
                f"Module {module.id} allows unknown machine {machine_id}",
            )

    for producer in definitions.producers.values():
        for node_type in producer.allowed_node_types:
            _require_key(
                definitions.resource_nodes,
                node_type,
                f"Producer {producer.id} allows unknown resource node {node_type}",
            )
        for machine_id in producer.allowed_machine_types:
            _require_key(
                definitions.machines,
                machine_id,
                f"Producer {producer.id} allows unknown machine {machine_id}",
            )
        _validate_producer_levels(producer.id, producer.levels)


def _templates_root() -> Path:
    return Path(__file__).resolve().parents[3] / "templates"


def _load_json_object(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise DefinitionLoadError(f"Missing definition file: {path}")

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise DefinitionLoadError(f"Invalid JSON in {path}: {exc}") from exc

    if not isinstance(data, dict):
        raise DefinitionLoadError(f"Definition file must contain an object: {path}")

    return data


def _validate_mapping_ids(label: str, items: dict[str, Any]) -> None:
    for item_id, item in items.items():
        if getattr(item, "id", item_id) != item_id:
            raise DefinitionLoadError(
                f"{label} id mismatch: key {item_id} != id {item.id}"
            )


def _validate_factory_levels(
    factory_levels: dict[int, FactoryLevelDefinition],
) -> None:
    for level, level_definition in factory_levels.items():
        if level_definition.level != level:
            raise DefinitionLoadError(
                f"Factory level mismatch: key {level} != level {level_definition.level}"
            )
        if level <= 0:
            raise DefinitionLoadError(f"Factory level must be positive: {level}")
        if level_definition.module_slots <= 0:
            raise DefinitionLoadError(
                f"Factory level {level} must define positive module_slots"
            )
        if level_definition.machine_slots_per_module <= 0:
            raise DefinitionLoadError(
                f"Factory level {level} must define positive machine_slots_per_module"
            )


def _validate_producer_levels(producer_id: str, levels: dict[int, Any]) -> None:
    if not levels:
        raise DefinitionLoadError(f"Producer {producer_id} must define levels")

    for level, level_definition in levels.items():
        if level_definition.level != level:
            raise DefinitionLoadError(
                f"Producer {producer_id} level mismatch: "
                f"key {level} != level {level_definition.level}"
            )
        if level <= 0:
            raise DefinitionLoadError(
                f"Producer {producer_id} level must be positive: {level}"
            )
        if level_definition.machine_slots <= 0:
            raise DefinitionLoadError(
                f"Producer {producer_id} level {level} must define positive machine_slots"
            )


def _require_key(items: dict[str, Any], key: str, message: str) -> None:
    if key not in items:
        raise DefinitionLoadError(message)
