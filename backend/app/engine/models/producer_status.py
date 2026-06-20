from enum import Enum


class ProducerStatus(str, Enum):
    IDLE = "idle"
    WORKING = "working"
    UNDERPOWERED = "underpowered"
    DEPLETED = "depleted"
    INVALID_NODE = "invalid_node"
    INSUFFICIENT_LEVEL = "insufficient_level"
