from app.engine.models.factory_level_definition import FactoryLevelDefinition


FACTORY_LEVEL_DEFINITIONS = {
    1: FactoryLevelDefinition(
        level=1,
        module_slots=2,
        machine_slots_per_module=2,
        upgrade_cost={},
    ),
    2: FactoryLevelDefinition(
        level=2,
        module_slots=3,
        machine_slots_per_module=4,
        upgrade_cost={
            "andesite_alloy": 8,
            "iron_sheet": 6,
            "shaft": 4,
        },
    ),
    3: FactoryLevelDefinition(
        level=3,
        module_slots=4,
        machine_slots_per_module=6,
        upgrade_cost={
            "andesite_alloy": 16,
            "iron_sheet": 12,
            "copper_sheet": 8,
            "machine_parts": 2,
        },
    ),
}
