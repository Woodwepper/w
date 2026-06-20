from typing import Any

from app.engine.instances.machine_instance import MachineInstance
from app.engine.instances.power_network import PowerNetwork
from app.engine.instances.su_source_instance import SUSourceInstance
from app.engine.models.producer_building import ProducerBuilding
from app.engine.models.producer_status import ProducerStatus
from app.engine.models.factory_building import FactoryBuilding
from app.engine.models.factory_status import FactoryStatus
from app.engine.models.world import World
from app.engine.producers import (
    calculate_producer_su_required as calculate_power_producer_su_required,
)


def calculate_su_source_output(
    world: World,
    source: SUSourceInstance | Any,
) -> int:
    if hasattr(source, "enabled") and not source.enabled:
        return 0

    if getattr(source, "status", "active") != "active":
        return 0

    source_type = getattr(source, "source_type", None)
    if source_type is None:
        return getattr(source, "su_output", 0)

    source_definition = world.definitions.get_su_source(source_type)
    if source_definition is None:
        return 0

    return source_definition.su_output


def calculate_machine_su_required(
    world: World,
    machine: MachineInstance,
) -> int:
    machine_definition = world.definitions.get_machine(machine.machine_type)
    if machine_definition is None:
        return 0

    return machine_definition.su_cost


def calculate_factory_su_required(
    world: World,
    factory: FactoryBuilding,
) -> int:
    total = 0

    for module in factory.modules:
        for machine in module.installed_machines:
            total += calculate_machine_su_required(world, machine)

    return total


def calculate_producer_su_required(
    world: World,
    producer: ProducerBuilding,
) -> int:
    return calculate_power_producer_su_required(world, producer)


def calculate_network_su_output(
    world: World,
    network: PowerNetwork,
) -> int:
    total = 0

    for source_id in network.source_ids:
        source = world.get_su_source(source_id)
        if source is None:
            continue
        total += calculate_su_source_output(world, source)

    return total


def get_network_consumers(
    world: World,
    network: PowerNetwork,
) -> list[FactoryBuilding | ProducerBuilding]:
    consumers: list[FactoryBuilding | ProducerBuilding] = []

    for consumer_ref in network.consumers:
        if consumer_ref.consumer_type == "factory":
            factory = world.get_factory(consumer_ref.consumer_id)
            if factory is not None:
                consumers.append(factory)
            continue

        if consumer_ref.consumer_type == "producer":
            producer = world.get_producer(consumer_ref.consumer_id)
            if producer is not None:
                consumers.append(producer)

    return consumers


def calculate_consumer_su_required(
    world: World,
    consumer: FactoryBuilding | ProducerBuilding,
) -> int:
    if isinstance(consumer, FactoryBuilding):
        return calculate_factory_su_required(world, consumer)

    return calculate_producer_su_required(world, consumer)


def mark_consumer_powered(
    consumer: FactoryBuilding | ProducerBuilding,
) -> None:
    if isinstance(consumer, FactoryBuilding):
        consumer.status = FactoryStatus.IDLE
        return

    consumer.status = ProducerStatus.IDLE


def get_consumer_power_key(
    consumer: FactoryBuilding | ProducerBuilding,
) -> tuple[str, int]:
    if isinstance(consumer, FactoryBuilding):
        return ("factory", consumer.id)

    return ("producer", consumer.id)


def allocate_power(world: World) -> None:
    for factory in world.factories:
        factory.status = FactoryStatus.UNDERPOWERED

    for producer in world.producers:
        producer.status = ProducerStatus.UNDERPOWERED

    powered_consumers: set[tuple[str, int]] = set()

    for network in world.power_networks:
        remaining_su = calculate_network_su_output(world, network)
        consumers = sorted(
            get_network_consumers(world, network),
            key=lambda consumer: consumer.priority,
        )

        for consumer in consumers:
            consumer_key = get_consumer_power_key(consumer)
            if consumer_key in powered_consumers:
                continue

            required_su = calculate_consumer_su_required(world, consumer)
            if remaining_su >= required_su:
                mark_consumer_powered(consumer)
                powered_consumers.add(consumer_key)
                remaining_su -= required_su
