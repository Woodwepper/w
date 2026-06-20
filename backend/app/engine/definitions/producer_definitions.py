from app.engine.models.producer_definition import ProducerDefinition


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
        machine_id="mechanical_drill",
        icon="mine",
        visual_key="mine",
    ),
    "quarry": ProducerDefinition(
        id="quarry",
        name="Quarry",
        allowed_node_types=["stone_outcrop"],
        base_duration=5.0,
        base_output_amount=1,
        machine_id="mechanical_drill",
        icon="quarry",
        visual_key="quarry",
    ),
    "lumber_camp": ProducerDefinition(
        id="lumber_camp",
        name="Lumber Camp",
        allowed_node_types=["forest"],
        base_duration=6.0,
        base_output_amount=1,
        machine_id="mechanical_saw",
        icon="lumber",
        visual_key="lumber_camp",
    ),
    "water_pump": ProducerDefinition(
        id="water_pump",
        name="Water Pump",
        allowed_node_types=["water_source"],
        base_duration=4.0,
        base_output_amount=1,
        machine_id="mechanical_pump",
        icon="pump",
        visual_key="water_pump",
    ),
}
