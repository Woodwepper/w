from typing import Any

from app.engine.systems.construction import (
    build_machine_from_resources,
    can_build_machine_from_resources,
    upgrade_machine,
)
from app.engine.entities.machine_instance import MachineInstance
from app.engine.core.statuses import MachineStatus
from app.engine.entities.producer_building import ProducerBuilding
from app.engine.definitions.producer_definition import ProducerDefinition
from app.engine.core.statuses import ProducerStatus
from app.engine.entities.resource_node import ResourceNode
from app.engine.core.world import World


def calculate_producer_su_required(
    world: World,
    producer: ProducerBuilding,
) -> int:
    total = 0

    for machine in producer.installed_machines:
        machine_definition = world.definitions.get_machine(machine.machine_type)
        if machine_definition is None:
            continue
        total += machine_definition.su_cost

    return total


def can_install_machine_in_producer(
    producer: ProducerBuilding | None,
    machine: MachineInstance | None,
    definitions,
) -> bool:
    if producer is None or machine is None:
        return False

    producer_definition = definitions.get_producer(producer.producer_type)
    if producer_definition is None:
        return False

    machine_definition = definitions.get_machine(machine.machine_type)
    if machine_definition is None:
        return False

    if machine.machine_type not in producer_definition.allowed_machine_types:
        return False

    if producer.get_machine(machine.id) is not None:
        return False

    if len(producer.installed_machines) >= producer.get_machine_slot_limit(definitions):
        return False

    return True


def install_machine_in_producer(
    producer: ProducerBuilding | None,
    machine: MachineInstance,
    definitions,
) -> bool:
    if not can_install_machine_in_producer(producer, machine, definitions):
        return False

    producer.add_machine(machine)
    return True


def build_and_install_machine_in_producer_from_resources(
    world: World | None,
    producer_id: int,
    machine_type: str,
    machine_id: int,
    level: int = 1,
    metadata: dict[str, Any] | None = None,
) -> bool:
    if world is None:
        return False

    producer = world.get_producer(producer_id)
    if producer is None:
        return False

    proposed_machine = MachineInstance(
        id=machine_id,
        machine_type=machine_type,
        level=max(1, level),
        metadata=dict(metadata or {}),
    )
    if not can_install_machine_in_producer(
        producer,
        proposed_machine,
        world.definitions,
    ):
        return False

    if not can_build_machine_from_resources(
        world.inventory,
        world.definitions,
        machine_type,
    ):
        return False

    machine = build_machine_from_resources(
        world.inventory,
        world.definitions,
        machine_type,
        machine_id,
        level=level,
        metadata=metadata,
    )
    if machine is None:
        return False

    producer.add_machine(machine)
    return True


def upgrade_producer_machine(
    inventory: dict[str, int],
    definitions,
    machine: MachineInstance,
    target_level: int,
) -> bool:
    return upgrade_machine(inventory, definitions, machine, target_level)


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
        _idle_producer_machines(producer)
        return

    node_definition = world.definitions.get_resource_node_definition(node.node_type)
    if node_definition is None:
        producer.status = ProducerStatus.INVALID_NODE
        _idle_producer_machines(producer)
        return

    if node.node_type not in producer_definition.allowed_node_types:
        producer.status = ProducerStatus.INVALID_NODE
        _idle_producer_machines(producer)
        return

    if node.is_depleted():
        producer.status = ProducerStatus.DEPLETED
        _idle_producer_machines(producer)
        return

    machine_results = []
    for machine in producer.installed_machines:
        if node.is_depleted():
            machine.status = MachineStatus.IDLE
            continue
        machine_results.append(
            process_producer_machine(
                world,
                producer,
                node,
                machine,
                seconds,
            )
        )

    if node.is_depleted():
        producer.status = ProducerStatus.DEPLETED
    elif any(result == "working" for result in machine_results):
        producer.status = ProducerStatus.WORKING
    elif any(result == "insufficient_level" for result in machine_results):
        producer.status = ProducerStatus.INSUFFICIENT_LEVEL
    else:
        producer.status = ProducerStatus.IDLE


def process_producer_machine(
    world: World,
    producer: ProducerBuilding,
    node: ResourceNode,
    machine: MachineInstance,
    seconds: float,
) -> str:
    if machine.status == MachineStatus.UNDERPOWERED:
        return "underpowered"

    producer_definition = world.definitions.get_producer(producer.producer_type)
    node_definition = world.definitions.get_resource_node_definition(node.node_type)
    machine_definition = world.definitions.get_machine(machine.machine_type)
    if (
        producer_definition is None
        or node_definition is None
        or machine_definition is None
        or machine.machine_type not in producer_definition.allowed_machine_types
    ):
        machine.status = MachineStatus.MISSING_MACHINE
        return "invalid_machine"

    if machine.level < node.required_machine_level:
        machine.status = MachineStatus.IDLE
        return "insufficient_level"

    if node.is_depleted():
        machine.status = MachineStatus.IDLE
        machine.clear_progress()
        return "depleted"

    effective_duration = (
        producer_definition.base_duration
        * node.hardness
        / machine_definition.get_speed_multiplier(machine.level)
    )
    if effective_duration <= 0:
        machine.status = MachineStatus.IDLE
        return "invalid_machine"

    machine.progress += seconds
    completed_cycles = int(machine.progress // effective_duration)
    if completed_cycles <= 0:
        machine.status = MachineStatus.WORKING
        return "working"

    output_amount = (
        producer_definition.base_output_amount
        * node.richness
        * completed_cycles
    )
    output_amount = _clamp_output_to_remaining_node_amount(node, output_amount)
    if output_amount <= 0:
        machine.status = MachineStatus.IDLE
        machine.clear_progress()
        return "depleted"

    producer.add_output_item(node_definition.resource_type, output_amount)
    _consume_node_amount(node, output_amount)
    machine.progress = machine.progress % effective_duration
    machine.status = MachineStatus.WORKING

    if node.is_depleted():
        machine.clear_progress()
        return "depleted"

    return "working"


def _idle_producer_machines(producer: ProducerBuilding) -> None:
    for machine in producer.installed_machines:
        if machine.status == MachineStatus.UNDERPOWERED:
            continue
        machine.status = MachineStatus.IDLE


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
