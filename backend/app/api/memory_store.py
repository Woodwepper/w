from fastapi import HTTPException

from app.engine.entities.machine_instance import MachineInstance
from app.engine.entities.module_instance import ModuleInstance
from app.engine.entities.power_network import PowerNetwork
from app.engine.entities.su_source_instance import SUSourceInstance
from app.engine.entities.factory_building import FactoryBuilding
from app.engine.entities.producer_building import ProducerBuilding
from app.engine.entities.resource_node import ResourceNode
from app.engine.core.world import World


worlds: dict[int, World] = {}

next_world_id = 1
next_factory_id = 1
next_module_id = 1
next_machine_id = 1
next_su_source_id = 1
next_power_network_id = 1
next_resource_node_id = 1
next_producer_id = 1


def allocate_world_id() -> int:
    global next_world_id

    new_id = next_world_id
    next_world_id += 1
    return new_id


def allocate_factory_id() -> int:
    global next_factory_id

    new_id = next_factory_id
    next_factory_id += 1
    return new_id


def allocate_module_id() -> int:
    global next_module_id

    new_id = next_module_id
    next_module_id += 1
    return new_id


def allocate_machine_id() -> int:
    global next_machine_id

    new_id = next_machine_id
    next_machine_id += 1
    return new_id


def allocate_su_source_id() -> int:
    global next_su_source_id

    new_id = next_su_source_id
    next_su_source_id += 1
    return new_id


def allocate_power_network_id() -> int:
    global next_power_network_id

    new_id = next_power_network_id
    next_power_network_id += 1
    return new_id


def allocate_resource_node_id() -> int:
    global next_resource_node_id

    new_id = next_resource_node_id
    next_resource_node_id += 1
    return new_id


def allocate_producer_id() -> int:
    global next_producer_id

    new_id = next_producer_id
    next_producer_id += 1
    return new_id


def create_world(name: str) -> World:
    world = World(
        id=allocate_world_id(),
        name=name,
    )
    worlds[world.id] = world
    return world


def get_world_or_404(world_id: int) -> World:
    world = worlds.get(world_id)
    if world is None:
        raise HTTPException(status_code=404, detail="World not found")
    return world


def get_factory_or_404(
    world: World,
    factory_id: int,
) -> FactoryBuilding:
    factory = world.get_factory(factory_id)
    if factory is None:
        raise HTTPException(status_code=404, detail="Factory not found")
    return factory


def get_module_or_404(
    factory: FactoryBuilding,
    module_id: int,
) -> ModuleInstance:
    module = factory.get_module(module_id)
    if module is None:
        raise HTTPException(status_code=404, detail="Module not found")
    return module


def get_machine_or_404(
    module: ModuleInstance,
    machine_id: int,
) -> MachineInstance:
    machine = module.get_machine(machine_id)
    if machine is None:
        raise HTTPException(status_code=404, detail="Machine not found")
    return machine


def get_su_source_or_404(
    world: World,
    source_id: int,
) -> SUSourceInstance:
    su_source = world.get_su_source(source_id)
    if su_source is None:
        raise HTTPException(status_code=404, detail="SU source not found")
    return su_source


def get_power_network_or_404(
    world: World,
    network_id: int,
) -> PowerNetwork:
    power_network = world.get_power_network(network_id)
    if power_network is None:
        raise HTTPException(status_code=404, detail="Power network not found")
    return power_network


def get_resource_node_or_404(
    world: World,
    node_id: int,
) -> ResourceNode:
    resource_node = world.get_resource_node(node_id)
    if resource_node is None:
        raise HTTPException(status_code=404, detail="Resource node not found")
    return resource_node


def get_producer_or_404(
    world: World,
    producer_id: int,
) -> ProducerBuilding:
    producer = world.get_producer(producer_id)
    if producer is None:
        raise HTTPException(status_code=404, detail="Producer not found")
    return producer


def get_producer_machine_or_404(
    producer: ProducerBuilding,
    machine_id: int,
) -> MachineInstance:
    machine = producer.get_machine(machine_id)
    if machine is None:
        raise HTTPException(status_code=404, detail="Machine not found")
    return machine
