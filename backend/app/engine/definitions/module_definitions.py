from app.engine.models.module_definition import ModuleDefinition


MACHINE_COUNT_BY_LEVEL = {
    1: 2,
    2: 4,
    3: 6,
}

EFFICIENCY_MULTIPLIER_BY_LEVEL = {
    1: 1.0,
    2: 0.8,
    3: 0.6,
}


MODULE_DEFINITIONS = {
    "pressing_line": ModuleDefinition(
        id="pressing_line",
        name="Pressing Line",
        allowed_machine_types=["mechanical_press"],
        allowed_recipes=[
            "press_iron_sheet",
            "press_copper_sheet",
            "press_iron_plate",
            "press_copper_plate",
            "press_iron_bolt",
            "press_copper_wire",
        ],
        icon="press",
        visual_key="pressing_line",
    ),
    "crushing_line": ModuleDefinition(
        id="crushing_line",
        name="Crushing Line",
        allowed_machine_types=["crushing_wheel"],
        allowed_recipes=[
            "crush_raw_iron",
            "crush_raw_copper",
            "crush_stone",
            "crush_gravel",
            "crush_andesite",
        ],
        icon="crusher",
        visual_key="crushing_line",
    ),
    "smelting_line": ModuleDefinition(
        id="smelting_line",
        name="Smelting Line",
        allowed_machine_types=["mechanical_smelter"],
        allowed_recipes=[
            "smelt_crushed_iron",
            "smelt_crushed_copper",
            "smelt_sand_to_glass",
            "smelt_clay_to_brick",
            "smelt_cobblestone",
        ],
        icon="smelter",
        visual_key="smelting_line",
    ),
    "mixing_line": ModuleDefinition(
        id="mixing_line",
        name="Mixing Line",
        allowed_machine_types=["mechanical_mixer"],
        allowed_recipes=[
            "mix_andesite_alloy",
            "mix_conductive_alloy",
            "mix_construction_blend",
            "mix_industrial_compound",
            "mix_machine_base",
        ],
        icon="mixer",
        visual_key="mixing_line",
    ),
    "assembling_line": ModuleDefinition(
        id="assembling_line",
        name="Assembling Line",
        allowed_machine_types=["mechanical_assembler"],
        allowed_recipes=[
            "assemble_shaft",
            "assemble_cogwheel",
            "assemble_large_cogwheel",
            "assemble_machine_parts",
            "assemble_basic_mechanism",
        ],
        icon="assembler",
        visual_key="assembling_line",
    ),
}
