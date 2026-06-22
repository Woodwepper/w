from app.engine.definitions.su_source_definition import SUSourceDefinition


SU_SOURCE_DEFINITIONS = {
    "water_wheel": SUSourceDefinition(
        id="water_wheel",
        name="Water Wheel",
        su_output=4096,
    ),
    "windmill": SUSourceDefinition(
        id="windmill",
        name="Windmill",
        su_output=2048,
    ),
    "steam_engine": SUSourceDefinition(
        id="steam_engine",
        name="Steam Engine",
        su_output=8192,
    ),
}
