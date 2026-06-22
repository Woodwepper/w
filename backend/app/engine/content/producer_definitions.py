from app.engine.definitions.producer_definition import ProducerDefinition
from app.engine.definitions.producer_level_definition import ProducerLevelDefinition


DEFAULT_LEVELS = {
    1: ProducerLevelDefinition(
        level=1,
        machine_slots=2,
        upgrade_cost={},
    ),
    2: ProducerLevelDefinition(
        level=2,
        machine_slots=4,
        upgrade_cost={
            "andesite_alloy": 8,
            "iron_sheet": 6,
            "shaft": 4,
        },
    ),
    3: ProducerLevelDefinition(
        level=3,
        machine_slots=6,
        upgrade_cost={
            "andesite_alloy": 16,
            "iron_sheet": 12,
            "machine_parts": 2,
        },
    ),
}


PRODUCER_DEFINITIONS = {
    "mine": ProducerDefinition(
        id="mine",
        name="Mine",
        allowed_node_types=[
            "iron_deposit",
            "copper_deposit",
            "coal_vein",
        ],
        base_duration=5.0,
        base_output_amount=1,
        allowed_machine_types=["mechanical_drill"],
        levels=DEFAULT_LEVELS,
        icon="mine",
        visual_key="mine",
    ),
    "quarry": ProducerDefinition(
        id="quarry",
        name="Quarry",
        allowed_node_types=["stone_outcrop"],
        base_duration=5.0,
        base_output_amount=1,
        allowed_machine_types=["mechanical_drill"],
        levels=DEFAULT_LEVELS,
        icon="quarry",
        visual_key="quarry",
    ),
    "lumber_camp": ProducerDefinition(
        id="lumber_camp",
        name="Lumber Camp",
        allowed_node_types=["forest"],
        base_duration=6.0,
        base_output_amount=1,
        allowed_machine_types=["mechanical_saw"],
        levels=DEFAULT_LEVELS,
        icon="lumber",
        visual_key="lumber_camp",
    ),
    "water_pump": ProducerDefinition(
        id="water_pump",
        name="Water Pump",
        allowed_node_types=["water_source"],
        base_duration=4.0,
        base_output_amount=1,
        allowed_machine_types=["mechanical_pump"],
        levels=DEFAULT_LEVELS,
        icon="pump",
        visual_key="water_pump",
    ),
}
