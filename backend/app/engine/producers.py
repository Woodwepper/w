from app.engine.models.producer_building import ProducerBuilding
from app.engine.models.producer_definition import ProducerDefinition
from app.engine.models.producer_status import ProducerStatus
from app.engine.models.resource_node import ResourceNode
from app.engine.models.world import World


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


def get_producer_machine_count(producer: ProducerBuilding) -> int:
    return MACHINE_COUNT_BY_LEVEL.get(producer.machine_level, MACHINE_COUNT_BY_LEVEL[1])


def get_producer_efficiency_multiplier(producer: ProducerBuilding) -> float:
    return EFFICIENCY_MULTIPLIER_BY_LEVEL.get(
        producer.efficiency_level,
        EFFICIENCY_MULTIPLIER_BY_LEVEL[1],
    )


def calculate_producer_su_required(
    world: World,
    producer: ProducerBuilding,
) -> int:
    producer_definition = world.definitions.get_producer(producer.producer_type)
    if producer_definition is None:
        return 0

    machine_definition = world.definitions.get_machine(producer_definition.machine_id)
    if machine_definition is None:
        return 0

    return machine_definition.su_cost * get_producer_machine_count(producer)


def process_producers(world: World, seconds: float) -> None:
    for producer in world.producers:
        process_producer(world, producer, seconds)


def process_producer(
    world: World,
    producer: ProducerBuilding,
    seconds: float,
) -> None:
    if seconds <= 0:
        return

    if producer.status == ProducerStatus.UNDERPOWERED:
        return

    producer_definition = world.definitions.get_producer(producer.producer_type)
    node = world.get_resource_node(producer.resource_node_id)
    if producer_definition is None or node is None:
        producer.status = ProducerStatus.INVALID_NODE
        return

    node_definition = world.definitions.get_resource_node_definition(node.node_type)
    if node_definition is None:
        producer.status = ProducerStatus.INVALID_NODE
        return

    if node.node_type not in producer_definition.allowed_node_types:
        producer.status = ProducerStatus.INVALID_NODE
        return

    if producer.machine_level < node.required_machine_level:
        producer.status = ProducerStatus.INSUFFICIENT_LEVEL
        return

    if node.is_depleted():
        producer.status = ProducerStatus.DEPLETED
        return

    final_duration = _get_final_duration(producer, producer_definition, node)
    if final_duration <= 0:
        producer.status = ProducerStatus.INVALID_NODE
        return

    producer.progress += seconds
    completed_cycles = int(producer.progress // final_duration)
    if completed_cycles <= 0:
        producer.status = ProducerStatus.WORKING
        return

    output_amount = _calculate_output_amount(
        producer,
        producer_definition,
        node,
        completed_cycles,
    )
    output_amount = _clamp_output_to_remaining_node_amount(node, output_amount)
    if output_amount <= 0:
        producer.status = ProducerStatus.DEPLETED
        producer.progress = 0.0
        return

    producer.add_output_item(node_definition.resource_type, output_amount)
    _consume_node_amount(node, output_amount)
    producer.progress = producer.progress % final_duration

    if node.is_depleted():
        producer.status = ProducerStatus.DEPLETED
    else:
        producer.status = ProducerStatus.WORKING


def _get_final_duration(
    producer: ProducerBuilding,
    producer_definition: ProducerDefinition,
    node: ResourceNode,
) -> float:
    return (
        producer_definition.base_duration
        * node.hardness
        * get_producer_efficiency_multiplier(producer)
    )


def _calculate_output_amount(
    producer: ProducerBuilding,
    producer_definition: ProducerDefinition,
    node: ResourceNode,
    completed_cycles: int,
) -> int:
    return (
        producer_definition.base_output_amount
        * get_producer_machine_count(producer)
        * node.richness
        * completed_cycles
    )


def _clamp_output_to_remaining_node_amount(
    node: ResourceNode,
    output_amount: int,
) -> int:
    if node.infinite or node.remaining_amount is None:
        return output_amount

    return min(output_amount, max(0, node.remaining_amount))


def _consume_node_amount(
    node: ResourceNode,
    output_amount: int,
) -> None:
    if node.infinite or node.remaining_amount is None:
        return

    node.remaining_amount = max(0, node.remaining_amount - output_amount)
