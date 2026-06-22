from app.engine.entities.factory_building import FactoryBuilding
from app.engine.core.statuses import FactoryStatus
from app.engine.core.statuses import MachineStatus
from app.engine.entities.producer_building import ProducerBuilding
from app.engine.core.statuses import ProducerStatus
from app.engine.core.world import World
from app.engine.systems.power import (
    allocate_power,
    calculate_factory_su_required as calculate_power_factory_su_required,
    calculate_network_su_output,
    calculate_producer_su_required as calculate_power_producer_su_required,
)
from app.engine.systems.producers import process_producer
from app.engine.systems.production import process_factory


def calculate_su_produced(world: World) -> int:
    total = 0

    for network in world.power_networks:
        total += calculate_network_su_output(world, network)

    return total


def calculate_factory_su_required(
    world: World,
    factory: FactoryBuilding,
) -> int:
    return calculate_power_factory_su_required(world, factory)


def calculate_producer_su_required(
    world: World,
    producer: ProducerBuilding,
) -> int:
    return calculate_power_producer_su_required(world, producer)


def calculate_su_required(world: World) -> int:
    total = 0

    for factory in world.factories:
        total += calculate_factory_su_required(world, factory)

    for producer in world.producers:
        total += calculate_producer_su_required(world, producer)

    return total


def update_world_su(world: World) -> None:
    world.su_produced = calculate_su_produced(world)
    world.su_required = calculate_su_required(world)
    world.su_available = world.su_produced - world.su_required


def set_factory_underpowered(factory: FactoryBuilding) -> None:
    factory.status = FactoryStatus.UNDERPOWERED

    for module in factory.modules:
        module.status = FactoryStatus.UNDERPOWERED

        for machine in module.installed_machines:
            machine.status = MachineStatus.UNDERPOWERED


def clear_factory_underpowered(factory: FactoryBuilding) -> None:
    if factory.status == FactoryStatus.UNDERPOWERED:
        factory.status = FactoryStatus.IDLE

    for module in factory.modules:
        if module.status == FactoryStatus.UNDERPOWERED:
            module.status = FactoryStatus.IDLE

        for machine in module.installed_machines:
            if machine.status == MachineStatus.UNDERPOWERED:
                machine.status = MachineStatus.IDLE


def set_producer_underpowered(producer: ProducerBuilding) -> None:
    producer.status = ProducerStatus.UNDERPOWERED

    for machine in producer.installed_machines:
        machine.status = MachineStatus.UNDERPOWERED


def clear_producer_underpowered(producer: ProducerBuilding) -> None:
    if producer.status == ProducerStatus.UNDERPOWERED:
        producer.status = ProducerStatus.IDLE

    for machine in producer.installed_machines:
        if machine.status == MachineStatus.UNDERPOWERED:
            machine.status = MachineStatus.IDLE


def tick(world: World, seconds: float) -> None:
    if seconds <= 0:
        return

    allocate_power(world)
    update_world_su(world)

    for factory in world.factories:
        if factory.status == FactoryStatus.UNDERPOWERED:
            set_factory_underpowered(factory)
            continue

        clear_factory_underpowered(factory)
        process_factory(world, factory, seconds)

    for producer in world.producers:
        if producer.status == ProducerStatus.UNDERPOWERED:
            set_producer_underpowered(producer)
            continue

        clear_producer_underpowered(producer)
        process_producer(world, producer, seconds)

    world.simulated_time += seconds
