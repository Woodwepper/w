import json
from pathlib import Path
from typing import Any

from app.engine.definitions.factory_level_definition import FactoryLevelDefinition
from app.engine.definitions.machine_definition import MachineDefinition
from app.engine.definitions.module_definition import ModuleDefinition
from app.engine.definitions.object_definition import ObjectDefinition
from app.engine.definitions.producer_definition import ProducerDefinition
from app.engine.definitions.recipe_definition import Recipe
from app.engine.definitions.resource_node_definition import ResourceNodeDefinition
from app.engine.definitions.su_producer_definition import SUProducerDefinition
from app.engine.definitions.su_unit_definition import SUUnitDefinition


class DefinitionLoadError(ValueError):
    pass


REQUIRED_TEMPLATE_FILES = {
    "machines": "machines.json",
    "objects": "objects.json",
    "modules": "modules.json",
    "recipes": "recipes.json",
    "su_units": "su_units.json",
    "su_producers": "su_producers.json",
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
        objects={
            object_id: ObjectDefinition.from_dict(data)
            for object_id, data in raw_data["objects"].items()
        },
        modules={
            module_id: ModuleDefinition.from_dict(data)
            for module_id, data in raw_data["modules"].items()
        },
        recipes={
            recipe_id: Recipe.from_dict(data)
            for recipe_id, data in raw_data["recipes"].items()
        },
        su_units={
            unit_id: SUUnitDefinition.from_dict(data)
            for unit_id, data in raw_data["su_units"].items()
        },
        su_producers={
            producer_id: SUProducerDefinition.from_dict(data)
            for producer_id, data in raw_data["su_producers"].items()
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
    _validate_mapping_ids("object", definitions.objects)
    _validate_mapping_ids("module", definitions.modules)
    _validate_mapping_ids("recipe", definitions.recipes)
    _validate_mapping_ids("su_unit", definitions.su_units)
    _validate_mapping_ids("su_producer", definitions.su_producers)
    _validate_mapping_ids("resource_node", definitions.resource_nodes)
    _validate_mapping_ids("producer", definitions.producers)
    _validate_factory_levels(definitions.factory_levels)
    _validate_object_definitions(definitions)

    for recipe in definitions.recipes.values():
        for machine_id in recipe.required_machines:
            _require_key(
                definitions.machines,
                machine_id,
                f"Recipe {recipe.id} requires unknown machine {machine_id}",
            )
        _validate_item_costs(
            definitions,
            recipe.input_items,
            f"Recipe {recipe.id} input",
        )
        _validate_item_costs(
            definitions,
            recipe.output_items,
            f"Recipe {recipe.id} output",
        )

    for machine in definitions.machines.values():
        _validate_item_costs(
            definitions,
            machine.build_cost,
            f"Machine {machine.id} build_cost",
        )
        for level, upgrade_cost in machine.upgrade_costs.items():
            _validate_item_costs(
                definitions,
                upgrade_cost,
                f"Machine {machine.id} upgrade_cost level {level}",
            )
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
        for level, level_definition in producer.levels.items():
            _validate_item_costs(
                definitions,
                level_definition.upgrade_cost,
                f"Producer {producer.id} upgrade_cost level {level}",
            )

    for su_producer in definitions.su_producers.values():
        for unit_type in su_producer.allowed_unit_types:
            _require_key(
                definitions.su_units,
                unit_type,
                f"SU producer {su_producer.id} allows unknown SU unit {unit_type}",
            )
        _validate_su_producer_levels(su_producer.id, su_producer.levels)
        for level, level_definition in su_producer.levels.items():
            _validate_item_costs(
                definitions,
                level_definition.upgrade_cost,
                f"SU producer {su_producer.id} upgrade_cost level {level}",
            )

    for level, level_definition in definitions.factory_levels.items():
        _validate_item_costs(
            definitions,
            level_definition.upgrade_cost,
            f"Factory level {level} upgrade_cost",
        )

    for resource_node in definitions.resource_nodes.values():
        _require_object(
            definitions,
            resource_node.resource_type,
            f"Resource node {resource_node.id} resource_type",
        )

    for su_unit in definitions.su_units.values():
        _validate_item_costs(
            definitions,
            su_unit.input_items,
            f"SU unit {su_unit.id} input",
        )
        _validate_item_costs(
            definitions,
            su_unit.build_cost,
            f"SU unit {su_unit.id} build_cost",
        )


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


def _validate_su_producer_levels(
    producer_id: str,
    levels: dict[int, Any],
) -> None:
    if not levels:
        raise DefinitionLoadError(f"SU producer {producer_id} must define levels")

    for level, level_definition in levels.items():
        if level_definition.level != level:
            raise DefinitionLoadError(
                f"SU producer {producer_id} level mismatch: "
                f"key {level} != level {level_definition.level}"
            )
        if level <= 0:
            raise DefinitionLoadError(
                f"SU producer {producer_id} level must be positive: {level}"
            )
        if level_definition.unit_slots <= 0:
            raise DefinitionLoadError(
                f"SU producer {producer_id} level {level} must define positive unit_slots"
            )


def _validate_object_definitions(definitions) -> None:
    supported_entity_types = {
        "machine",
        "producer",
        "su_producer",
        "su_unit",
    }

    for object_id, object_definition in definitions.objects.items():
        if object_definition.stack_kind == "normal":
            if object_definition.entity_type is not None:
                raise DefinitionLoadError(
                    f"Object {object_id} is normal but declares entity_type "
                    f"{object_definition.entity_type}"
                )
            continue

        if object_definition.stack_kind != "entity":
            raise DefinitionLoadError(
                f"Object {object_id} has unsupported stack_kind "
                f"{object_definition.stack_kind}"
            )

        entity_type = object_definition.entity_type
        if entity_type is None:
            raise DefinitionLoadError(
                f"Object {object_id} is entity but has no entity_type"
            )
        if entity_type not in supported_entity_types:
            raise DefinitionLoadError(
                f"Object {object_id} declares unsupported entity_type {entity_type}"
            )

        if entity_type == "machine":
            _require_key(
                definitions.machines,
                object_id,
                f"Object {object_id} declares entity_type machine but no MachineDefinition exists",
            )
        elif entity_type == "producer":
            _require_key(
                definitions.producers,
                object_id,
                f"Object {object_id} declares entity_type producer but no ProducerDefinition exists",
            )
        elif entity_type == "su_producer":
            _require_key(
                definitions.su_producers,
                object_id,
                f"Object {object_id} declares entity_type su_producer but no SUProducerDefinition exists",
            )
        elif entity_type == "su_unit":
            _require_key(
                definitions.su_units,
                object_id,
                f"Object {object_id} declares entity_type su_unit but no SUUnitDefinition exists",
            )


def _require_key(items: dict[str, Any], key: str, message: str) -> None:
    if key not in items:
        raise DefinitionLoadError(message)


def _validate_item_costs(definitions, items: dict[str, int], label: str) -> None:
    for item_id in items:
        _require_object(definitions, item_id, label)


def _require_object(definitions, object_id: str, label: str) -> None:
    object_definition = definitions.get_object(object_id)
    if object_definition is None:
        raise DefinitionLoadError(f"{label} uses unknown object {object_id}")
    if object_definition.stack_kind != "normal":
        raise DefinitionLoadError(f"{label} must use normal object {object_id}")
