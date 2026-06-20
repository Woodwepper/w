from enum import Enum


class FactoryStatus(str, Enum):
    IDLE = "idle"
    WORKING = "working"
    UNDERPOWERED = "underpowered"
    MISSING_INPUT = "missing_input"
    MISSING_MACHINE = "missing_machine"
    INVALID_RECIPE = "invalid_recipe"
