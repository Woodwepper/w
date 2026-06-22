from enum import Enum


class FactoryStatus(str, Enum):
    IDLE = "idle"
    WORKING = "working"
    UNDERPOWERED = "underpowered"
    MISSING_INPUT = "missing_input"
    MISSING_MACHINE = "missing_machine"
    INVALID_RECIPE = "invalid_recipe"


class MachineStatus(str, Enum):
    IDLE = "idle"
    WORKING = "working"
    UNDERPOWERED = "underpowered"
    MISSING_INPUT = "missing_input"
    MISSING_MACHINE = "missing_machine"
    INVALID_RECIPE = "invalid_recipe"


class ProducerStatus(str, Enum):
    IDLE = "idle"
    WORKING = "working"
    UNDERPOWERED = "underpowered"
    DEPLETED = "depleted"
    INVALID_NODE = "invalid_node"
    INSUFFICIENT_LEVEL = "insufficient_level"
