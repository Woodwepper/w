from app.engine.definitions.machine_definition import MachineDefinition


MACHINE_DEFINITIONS = {
    "mechanical_press": MachineDefinition(
        id="mechanical_press",
        name="Mechanical Press",
        su_cost=1024,
        build_cost={
            "andesite_alloy": 2,
            "iron_sheet": 1,
        },
        upgrade_costs={
            2: {"andesite_alloy": 4, "iron_sheet": 2},
            3: {"andesite_alloy": 8, "machine_parts": 1},
        },
        speed_multipliers={1: 1.0, 2: 1.25, 3: 1.5},
    ),
    "mechanical_mixer": MachineDefinition(
        id="mechanical_mixer",
        name="Mechanical Mixer",
        su_cost=2048,
        build_cost={
            "andesite_alloy": 3,
            "shaft": 2,
        },
        upgrade_costs={
            2: {"andesite_alloy": 6, "copper_sheet": 2},
            3: {"andesite_alloy": 10, "machine_parts": 1},
        },
        speed_multipliers={1: 1.0, 2: 1.25, 3: 1.5},
    ),
    "crushing_wheel": MachineDefinition(
        id="crushing_wheel",
        name="Crushing Wheel",
        su_cost=1536,
        build_cost={
            "andesite_alloy": 2,
            "shaft": 2,
        },
        upgrade_costs={
            2: {"andesite_alloy": 5, "iron_sheet": 2},
            3: {"andesite_alloy": 9, "machine_parts": 1},
        },
        speed_multipliers={1: 1.0, 2: 1.25, 3: 1.5},
    ),
    "mechanical_smelter": MachineDefinition(
        id="mechanical_smelter",
        name="Mechanical Smelter",
        su_cost=2048,
        build_cost={
            "andesite_alloy": 3,
            "brick": 4,
        },
        upgrade_costs={
            2: {"andesite_alloy": 6, "iron_sheet": 2},
            3: {"andesite_alloy": 10, "machine_parts": 1},
        },
        speed_multipliers={1: 1.0, 2: 1.25, 3: 1.5},
    ),
    "mechanical_assembler": MachineDefinition(
        id="mechanical_assembler",
        name="Mechanical Assembler",
        su_cost=3072,
        build_cost={
            "andesite_alloy": 4,
            "shaft": 2,
            "cogwheel": 2,
        },
        upgrade_costs={
            2: {"andesite_alloy": 8, "iron_sheet": 4},
            3: {"andesite_alloy": 12, "machine_parts": 2},
        },
        speed_multipliers={1: 1.0, 2: 1.25, 3: 1.5},
    ),
    "mechanical_drill": MachineDefinition(
        id="mechanical_drill",
        name="Mechanical Drill",
        su_cost=1024,
        build_cost={
            "andesite_alloy": 3,
            "iron_sheet": 2,
            "shaft": 1,
        },
        upgrade_costs={
            2: {"andesite_alloy": 5, "iron_sheet": 3},
            3: {"andesite_alloy": 8, "machine_parts": 1},
        },
        speed_multipliers={1: 1.0, 2: 1.25, 3: 1.5},
        icon="drill",
        visual_key="mechanical_drill",
    ),
    "mechanical_saw": MachineDefinition(
        id="mechanical_saw",
        name="Mechanical Saw",
        su_cost=768,
        build_cost={
            "andesite_alloy": 2,
            "iron_sheet": 1,
            "shaft": 1,
        },
        upgrade_costs={
            2: {"andesite_alloy": 4, "iron_sheet": 2},
            3: {"andesite_alloy": 7, "machine_parts": 1},
        },
        speed_multipliers={1: 1.0, 2: 1.25, 3: 1.5},
        icon="saw",
        visual_key="mechanical_saw",
    ),
    "mechanical_pump": MachineDefinition(
        id="mechanical_pump",
        name="Mechanical Pump",
        su_cost=512,
        build_cost={
            "andesite_alloy": 2,
            "copper_sheet": 1,
            "shaft": 1,
        },
        upgrade_costs={
            2: {"andesite_alloy": 3, "copper_sheet": 2},
            3: {"andesite_alloy": 6, "machine_parts": 1},
        },
        speed_multipliers={1: 1.0, 2: 1.25, 3: 1.5},
        icon="pump",
        visual_key="mechanical_pump",
    ),
}
