from dataclasses import asdict

from fastapi import APIRouter, HTTPException

from app.api import memory_store
from app.api.schemas import (
    AddFactoryInputRequest,
    AddInventoryItemRequest,
    AddNetworkConsumerRequest,
    AddNetworkSourceRequest,
    BuildInstallMachineRequest,
    CollectProducerOutputRequest,
    CollectOutputRequest,
    CreateFactoryRequest,
    CreateModuleRequest,
    CreatePowerNetworkRequest,
    CreateProducerRequest,
    CreateResourceNodeRequest,
    CreateSUSourceRequest,
    CreateWorldRequest,
    SetModuleRecipeRequest,
    TickRequest,
    UpdateFactoryRequest,
    UpgradeMachineRequest,
)
from app.engine.construction import (
    build_and_install_machine_from_resources,
    can_build_machine_from_resources,
    upgrade_machine,
)
from app.engine.instances.module_instance import ModuleInstance
from app.engine.instances.power_network import PowerNetwork, PowerConsumerRef
from app.engine.instances.su_source_instance import SUSourceInstance
from app.engine.models.factory_building import FactoryBuilding
from app.engine.models.producer_building import ProducerBuilding
from app.engine.models.resource_node import ResourceNode
from app.engine.producers import (
    EFFICIENCY_MULTIPLIER_BY_LEVEL,
    MACHINE_COUNT_BY_LEVEL,
)
from app.engine.models.world import World
from app.engine.simulation import tick


router = APIRouter(prefix="/api", tags=["Factory Lab API V2"])
SUPPORTED_POWER_CONSUMER_TYPES = {"factory", "producer"}


def bad_request(message: str) -> None:
    raise HTTPException(status_code=400, detail=message)


def validate_positive_amount(amount: int, field_name: str = "amount") -> None:
    if amount <= 0:
        bad_request(f"{field_name} must be greater than 0")


def validate_positive_seconds(seconds: float) -> None:
    if seconds <= 0:
        bad_request("seconds must be greater than 0")


def get_recipe_or_404(world: World, recipe_id: str):
    recipe = world.definitions.get_recipe(recipe_id)
    if recipe is None:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return recipe


def validate_module_type(world: World, module_type: str) -> None:
    if world.definitions.get_module(module_type) is None:
        bad_request("module_type does not exist")


def validate_recipe_for_module(
    world: World,
    module_type: str,
    recipe_id: str,
) -> None:
    get_recipe_or_404(world, recipe_id)

    module_definition = world.definitions.get_module(module_type)
    if module_definition is None:
        bad_request("module_type does not exist")

    if recipe_id not in module_definition.allowed_recipes:
        bad_request("Recipe is not compatible with this module")


def validate_machine_type(world: World, machine_type: str) -> None:
    if world.definitions.get_machine(machine_type) is None:
        bad_request("machine_type does not exist")


def validate_machine_allowed_in_module(
    world: World,
    module: ModuleInstance,
    machine_type: str,
) -> None:
    module_definition = world.definitions.get_module(module.module_type)
    if module_definition is None:
        bad_request("module_type does not exist")

    if machine_type not in module_definition.allowed_machine_types:
        bad_request("Machine type is not compatible with this module")


def validate_su_source_type(world: World, source_type: str) -> None:
    if world.definitions.get_su_source(source_type) is None:
        bad_request("source_type does not exist")


def validate_resource_node_type(world: World, node_type: str) -> None:
    if world.definitions.get_resource_node_definition(node_type) is None:
        bad_request("node_type does not exist")


def validate_producer_type(world: World, producer_type: str) -> None:
    if world.definitions.get_producer(producer_type) is None:
        bad_request("producer_type does not exist")


def validate_producer_levels(machine_level: int, efficiency_level: int) -> None:
    if machine_level not in MACHINE_COUNT_BY_LEVEL:
        bad_request("machine_level is not defined")
    if efficiency_level not in EFFICIENCY_MULTIPLIER_BY_LEVEL:
        bad_request("efficiency_level is not defined")


def validate_producer_can_use_node(
    world: World,
    producer_type: str,
    node_type: str,
) -> None:
    producer_definition = world.definitions.get_producer(producer_type)
    if producer_definition is None:
        bad_request("producer_type does not exist")

    if node_type not in producer_definition.allowed_node_types:
        bad_request("Producer type is not compatible with this resource node")


def validate_power_consumer_type(consumer_type: str) -> None:
    if consumer_type not in SUPPORTED_POWER_CONSUMER_TYPES:
        bad_request("consumer_type is not supported")


def validate_power_consumer_exists(
    world: World,
    consumer_type: str,
    consumer_id: int,
) -> None:
    validate_power_consumer_type(consumer_type)

    if consumer_type == "factory":
        memory_store.get_factory_or_404(world, consumer_id)
        return

    if consumer_type == "producer":
        memory_store.get_producer_or_404(world, consumer_id)


def network_has_consumer(
    network: PowerNetwork,
    consumer_type: str,
    consumer_id: int,
) -> bool:
    return PowerConsumerRef(
        consumer_type=consumer_type,
        consumer_id=consumer_id,
    ) in network.consumers


@router.post("/worlds")
def create_world(request: CreateWorldRequest):
    world = memory_store.create_world(request.name)
    return world.to_dict()


@router.get("/worlds")
def list_worlds():
    return {
        "worlds": [
            world.to_dict()
            for world in memory_store.worlds.values()
        ]
    }


@router.get("/worlds/{world_id}")
def get_world_state(world_id: int):
    world = memory_store.get_world_or_404(world_id)
    return world.to_dict()


@router.post("/worlds/{world_id}/tick")
def simulate_world(world_id: int, request: TickRequest):
    world = memory_store.get_world_or_404(world_id)
    validate_positive_seconds(request.seconds)

    tick(world, request.seconds)
    return world.to_dict()


@router.post(
    "/worlds/{world_id}/inventory/test-add",
    description=(
        "Temporary development/testing endpoint. Adds items directly to the "
        "world inventory until mines, producers, and logistics exist."
    ),
)
def test_add_inventory_item(
    world_id: int,
    request: AddInventoryItemRequest,
):
    world = memory_store.get_world_or_404(world_id)
    validate_positive_amount(request.amount)

    world.add_inventory_item(request.item_id, request.amount)
    return world.to_dict()


@router.get("/worlds/{world_id}/catalog/machines")
def list_world_machines(world_id: int):
    world = memory_store.get_world_or_404(world_id)
    return {
        "machines": [
            machine.to_dict()
            for machine in world.definitions.machines.values()
        ]
    }


@router.get("/worlds/{world_id}/catalog/modules")
def list_world_modules(world_id: int):
    world = memory_store.get_world_or_404(world_id)
    return {
        "modules": [
            asdict(module)
            for module in world.definitions.modules.values()
        ]
    }


@router.get("/worlds/{world_id}/catalog/recipes")
def list_world_recipes(world_id: int):
    world = memory_store.get_world_or_404(world_id)
    return {
        "recipes": [
            recipe.to_dict()
            for recipe in world.definitions.recipes.values()
        ]
    }


@router.get("/worlds/{world_id}/catalog/su-sources")
def list_world_su_sources(world_id: int):
    world = memory_store.get_world_or_404(world_id)
    return {
        "su_sources": [
            asdict(su_source)
            for su_source in world.definitions.su_sources.values()
        ]
    }


@router.get("/worlds/{world_id}/catalog/factory-levels")
def list_world_factory_levels(world_id: int):
    world = memory_store.get_world_or_404(world_id)
    return {
        "factory_levels": [
            asdict(factory_level)
            for factory_level in world.definitions.factory_levels.values()
        ]
    }


@router.get("/worlds/{world_id}/catalog/resource-nodes")
def list_world_resource_node_definitions(world_id: int):
    world = memory_store.get_world_or_404(world_id)
    return {
        "resource_nodes": [
            resource_node.to_dict()
            for resource_node in world.definitions.resource_nodes.values()
        ]
    }


@router.get("/worlds/{world_id}/catalog/producers")
def list_world_producer_definitions(world_id: int):
    world = memory_store.get_world_or_404(world_id)
    return {
        "producers": [
            producer.to_dict()
            for producer in world.definitions.producers.values()
        ]
    }


@router.post(
    "/worlds/{world_id}/resource-nodes",
    description=(
        "Temporary development/testing endpoint. Creates natural resource "
        "nodes directly until map generation exists."
    ),
)
def create_resource_node(
    world_id: int,
    request: CreateResourceNodeRequest,
):
    world = memory_store.get_world_or_404(world_id)
    validate_resource_node_type(world, request.node_type)

    node_definition = world.definitions.get_resource_node_definition(request.node_type)
    if request.infinite and node_definition is not None and not node_definition.can_be_infinite:
        bad_request("node_type cannot be infinite")
    if request.richness <= 0:
        bad_request("richness must be greater than 0")
    if request.hardness <= 0:
        bad_request("hardness must be greater than 0")
    if request.required_machine_level < 1:
        bad_request("required_machine_level must be greater than or equal to 1")
    if request.remaining_amount is not None and request.remaining_amount < 0:
        bad_request("remaining_amount cannot be negative")

    resource_node = ResourceNode(
        id=memory_store.allocate_resource_node_id(),
        node_type=request.node_type,
        name=request.name,
        x=request.x,
        y=request.y,
        richness=request.richness,
        hardness=request.hardness,
        required_machine_level=request.required_machine_level,
        remaining_amount=request.remaining_amount,
        infinite=request.infinite,
        traits=list(request.traits),
    )
    world.add_resource_node(resource_node)
    return resource_node.to_dict()


@router.get("/worlds/{world_id}/resource-nodes/{node_id}")
def get_resource_node(
    world_id: int,
    node_id: int,
):
    world = memory_store.get_world_or_404(world_id)
    resource_node = memory_store.get_resource_node_or_404(world, node_id)
    return resource_node.to_dict()


@router.delete("/worlds/{world_id}/resource-nodes/{node_id}")
def delete_resource_node(
    world_id: int,
    node_id: int,
):
    world = memory_store.get_world_or_404(world_id)
    memory_store.get_resource_node_or_404(world, node_id)

    world.remove_resource_node(node_id)
    return world.to_dict()


@router.post("/worlds/{world_id}/producers")
def create_producer(
    world_id: int,
    request: CreateProducerRequest,
):
    world = memory_store.get_world_or_404(world_id)
    validate_producer_type(world, request.producer_type)
    validate_producer_levels(request.machine_level, request.efficiency_level)
    resource_node = memory_store.get_resource_node_or_404(
        world,
        request.resource_node_id,
    )
    validate_producer_can_use_node(
        world,
        request.producer_type,
        resource_node.node_type,
    )

    producer = ProducerBuilding(
        id=memory_store.allocate_producer_id(),
        name=request.name,
        producer_type=request.producer_type,
        resource_node_id=resource_node.id,
        x=resource_node.x,
        y=resource_node.y,
        machine_level=request.machine_level,
        efficiency_level=request.efficiency_level,
        priority=request.priority,
    )
    world.add_producer(producer)
    return producer.to_dict()


@router.get("/worlds/{world_id}/producers/{producer_id}")
def get_producer(
    world_id: int,
    producer_id: int,
):
    world = memory_store.get_world_or_404(world_id)
    producer = memory_store.get_producer_or_404(world, producer_id)
    return producer.to_dict()


@router.delete("/worlds/{world_id}/producers/{producer_id}")
def delete_producer(
    world_id: int,
    producer_id: int,
):
    world = memory_store.get_world_or_404(world_id)
    memory_store.get_producer_or_404(world, producer_id)

    world.remove_producer(producer_id)
    for network in world.power_networks:
        network.remove_consumer("producer", producer_id)

    return world.to_dict()


@router.post("/worlds/{world_id}/producers/{producer_id}/collect-output")
def collect_producer_output(
    world_id: int,
    producer_id: int,
    request: CollectProducerOutputRequest,
):
    world = memory_store.get_world_or_404(world_id)
    producer = memory_store.get_producer_or_404(world, producer_id)
    validate_positive_amount(request.amount)

    if producer.get_output_amount(request.item_id) < request.amount:
        bad_request("Not enough producer output available")

    producer.remove_output_item(request.item_id, request.amount)
    world.add_inventory_item(request.item_id, request.amount)
    return world.to_dict()


@router.post("/worlds/{world_id}/factories")
def create_factory(
    world_id: int,
    request: CreateFactoryRequest,
):
    world = memory_store.get_world_or_404(world_id)
    factory = FactoryBuilding(
        id=memory_store.allocate_factory_id(),
        name=request.name,
        x=request.x,
        y=request.y,
        icon=request.icon,
        visual_theme=request.visual_theme,
        priority=request.priority,
    )
    world.add_factory(factory)
    return factory.to_dict()


@router.get("/worlds/{world_id}/factories/{factory_id}")
def get_factory(
    world_id: int,
    factory_id: int,
):
    world = memory_store.get_world_or_404(world_id)
    factory = memory_store.get_factory_or_404(world, factory_id)
    return factory.to_dict()


@router.patch("/worlds/{world_id}/factories/{factory_id}")
def update_factory(
    world_id: int,
    factory_id: int,
    request: UpdateFactoryRequest,
):
    world = memory_store.get_world_or_404(world_id)
    factory = memory_store.get_factory_or_404(world, factory_id)

    if request.name is not None:
        factory.name = request.name
    if request.icon is not None:
        factory.icon = request.icon
    if request.visual_theme is not None:
        factory.visual_theme = request.visual_theme
    if request.priority is not None:
        factory.priority = request.priority

    return factory.to_dict()


@router.post("/worlds/{world_id}/factories/{factory_id}/level-up")
def level_up_factory(
    world_id: int,
    factory_id: int,
):
    world = memory_store.get_world_or_404(world_id)
    factory = memory_store.get_factory_or_404(world, factory_id)

    if not factory.level_up(world.definitions, world.inventory):
        bad_request("Not enough resources or no next factory level")

    return world.to_dict()


@router.post("/worlds/{world_id}/factories/{factory_id}/inputs")
def add_factory_input(
    world_id: int,
    factory_id: int,
    request: AddFactoryInputRequest,
):
    world = memory_store.get_world_or_404(world_id)
    factory = memory_store.get_factory_or_404(world, factory_id)
    validate_positive_amount(request.amount)

    factory.add_input_item(request.item_id, request.amount)
    return factory.to_dict()


@router.post("/worlds/{world_id}/factories/{factory_id}/collect-output")
def collect_factory_output(
    world_id: int,
    factory_id: int,
    request: CollectOutputRequest,
):
    world = memory_store.get_world_or_404(world_id)
    factory = memory_store.get_factory_or_404(world, factory_id)
    validate_positive_amount(request.amount)

    if factory.get_output_amount(request.item_id) < request.amount:
        bad_request("Not enough output available")

    factory.remove_output_item(request.item_id, request.amount)
    world.add_inventory_item(request.item_id, request.amount)
    return world.to_dict()


@router.post("/worlds/{world_id}/factories/{factory_id}/modules")
def create_module(
    world_id: int,
    factory_id: int,
    request: CreateModuleRequest,
):
    world = memory_store.get_world_or_404(world_id)
    factory = memory_store.get_factory_or_404(world, factory_id)

    validate_module_type(world, request.module_type)
    if request.active_recipe is not None:
        validate_recipe_for_module(
            world,
            request.module_type,
            request.active_recipe,
        )

    module = ModuleInstance(
        id=memory_store.allocate_module_id(),
        module_type=request.module_type,
        active_recipe=request.active_recipe,
    )
    if not factory.add_module(module, world.definitions):
        bad_request("Factory module slot limit reached")

    return factory.to_dict()


@router.get("/worlds/{world_id}/factories/{factory_id}/modules/{module_id}")
def get_module(
    world_id: int,
    factory_id: int,
    module_id: int,
):
    world = memory_store.get_world_or_404(world_id)
    factory = memory_store.get_factory_or_404(world, factory_id)
    module = memory_store.get_module_or_404(factory, module_id)
    return module.to_dict()


@router.delete("/worlds/{world_id}/factories/{factory_id}/modules/{module_id}")
def delete_module(
    world_id: int,
    factory_id: int,
    module_id: int,
):
    world = memory_store.get_world_or_404(world_id)
    factory = memory_store.get_factory_or_404(world, factory_id)
    memory_store.get_module_or_404(factory, module_id)

    factory.remove_module(module_id)
    return factory.to_dict()


@router.post("/worlds/{world_id}/factories/{factory_id}/modules/{module_id}/recipe")
def set_module_recipe(
    world_id: int,
    factory_id: int,
    module_id: int,
    request: SetModuleRecipeRequest,
):
    world = memory_store.get_world_or_404(world_id)
    factory = memory_store.get_factory_or_404(world, factory_id)
    module = memory_store.get_module_or_404(factory, module_id)

    validate_recipe_for_module(world, module.module_type, request.recipe_id)
    module.set_active_recipe(request.recipe_id)
    return factory.to_dict()


@router.delete("/worlds/{world_id}/factories/{factory_id}/modules/{module_id}/recipe")
def clear_module_recipe(
    world_id: int,
    factory_id: int,
    module_id: int,
):
    world = memory_store.get_world_or_404(world_id)
    factory = memory_store.get_factory_or_404(world, factory_id)
    module = memory_store.get_module_or_404(factory, module_id)

    module.set_active_recipe(None)
    return factory.to_dict()


@router.post(
    "/worlds/{world_id}/factories/{factory_id}/modules/{module_id}/machines/build-install"
)
def build_install_machine(
    world_id: int,
    factory_id: int,
    module_id: int,
    request: BuildInstallMachineRequest,
):
    world = memory_store.get_world_or_404(world_id)
    factory = memory_store.get_factory_or_404(world, factory_id)
    module = memory_store.get_module_or_404(factory, module_id)

    if request.level < 1:
        bad_request("level must be greater than or equal to 1")

    validate_machine_type(world, request.machine_type)
    validate_machine_allowed_in_module(world, module, request.machine_type)

    if len(module.installed_machines) >= factory.get_machine_slot_limit_per_module(
        world.definitions
    ):
        bad_request("Module machine slot limit reached")

    if not can_build_machine_from_resources(
        world.inventory,
        world.definitions,
        request.machine_type,
    ):
        bad_request("Not enough resources to build machine")

    machine_id = memory_store.allocate_machine_id()
    installed = build_and_install_machine_from_resources(
        world,
        factory_id,
        module_id,
        request.machine_type,
        machine_id,
        level=request.level,
        metadata=request.metadata,
    )
    if not installed:
        bad_request("Could not build and install machine")

    return factory.to_dict()


@router.patch(
    "/worlds/{world_id}/factories/{factory_id}/modules/{module_id}/machines/{machine_id}/upgrade"
)
def upgrade_module_machine(
    world_id: int,
    factory_id: int,
    module_id: int,
    machine_id: int,
    request: UpgradeMachineRequest,
):
    world = memory_store.get_world_or_404(world_id)
    factory = memory_store.get_factory_or_404(world, factory_id)
    module = memory_store.get_module_or_404(factory, module_id)
    machine = memory_store.get_machine_or_404(module, machine_id)

    if not upgrade_machine(
        world.inventory,
        world.definitions,
        machine,
        request.target_level,
    ):
        bad_request("Machine cannot be upgraded to target_level")

    return factory.to_dict()


@router.delete(
    "/worlds/{world_id}/factories/{factory_id}/modules/{module_id}/machines/{machine_id}"
)
def delete_module_machine(
    world_id: int,
    factory_id: int,
    module_id: int,
    machine_id: int,
):
    world = memory_store.get_world_or_404(world_id)
    factory = memory_store.get_factory_or_404(world, factory_id)
    module = memory_store.get_module_or_404(factory, module_id)
    memory_store.get_machine_or_404(module, machine_id)

    module.remove_machine(machine_id)
    return factory.to_dict()


@router.post("/worlds/{world_id}/su-sources")
def create_su_source(
    world_id: int,
    request: CreateSUSourceRequest,
):
    world = memory_store.get_world_or_404(world_id)
    validate_su_source_type(world, request.source_type)

    # Temporary testing path: SU source build costs from SUSourceDefinition
    # will be charged in a future API phase.
    su_source = SUSourceInstance(
        id=memory_store.allocate_su_source_id(),
        source_type=request.source_type,
        name=request.name,
        x=request.x,
        y=request.y,
    )
    world.add_su_source(su_source)
    return su_source.to_dict()


@router.get("/worlds/{world_id}/su-sources/{source_id}")
def get_su_source(
    world_id: int,
    source_id: int,
):
    world = memory_store.get_world_or_404(world_id)
    su_source = memory_store.get_su_source_or_404(world, source_id)
    return su_source.to_dict()


@router.delete("/worlds/{world_id}/su-sources/{source_id}")
def delete_su_source(
    world_id: int,
    source_id: int,
):
    world = memory_store.get_world_or_404(world_id)
    memory_store.get_su_source_or_404(world, source_id)

    world.remove_su_source(source_id)
    for network in world.power_networks:
        network.remove_source(source_id)

    return world.to_dict()


@router.post("/worlds/{world_id}/power-networks")
def create_power_network(
    world_id: int,
    request: CreatePowerNetworkRequest,
):
    world = memory_store.get_world_or_404(world_id)
    power_network = PowerNetwork(
        id=memory_store.allocate_power_network_id(),
        name=request.name,
    )
    world.add_power_network(power_network)
    return power_network.to_dict()


@router.get("/worlds/{world_id}/power-networks/{network_id}")
def get_power_network(
    world_id: int,
    network_id: int,
):
    world = memory_store.get_world_or_404(world_id)
    power_network = memory_store.get_power_network_or_404(world, network_id)
    return power_network.to_dict()


@router.delete("/worlds/{world_id}/power-networks/{network_id}")
def delete_power_network(
    world_id: int,
    network_id: int,
):
    world = memory_store.get_world_or_404(world_id)
    memory_store.get_power_network_or_404(world, network_id)

    world.remove_power_network(network_id)
    return world.to_dict()


@router.post("/worlds/{world_id}/power-networks/{network_id}/sources")
def add_power_network_source(
    world_id: int,
    network_id: int,
    request: AddNetworkSourceRequest,
):
    world = memory_store.get_world_or_404(world_id)
    power_network = memory_store.get_power_network_or_404(world, network_id)
    memory_store.get_su_source_or_404(world, request.source_id)

    power_network.add_source(request.source_id)
    return power_network.to_dict()


@router.delete("/worlds/{world_id}/power-networks/{network_id}/sources/{source_id}")
def remove_power_network_source(
    world_id: int,
    network_id: int,
    source_id: int,
):
    world = memory_store.get_world_or_404(world_id)
    power_network = memory_store.get_power_network_or_404(world, network_id)
    memory_store.get_su_source_or_404(world, source_id)

    if not power_network.remove_source(source_id):
        raise HTTPException(status_code=404, detail="Power network source not found")

    return power_network.to_dict()


@router.post("/worlds/{world_id}/power-networks/{network_id}/consumers")
def add_power_network_consumer(
    world_id: int,
    network_id: int,
    request: AddNetworkConsumerRequest,
):
    world = memory_store.get_world_or_404(world_id)
    power_network = memory_store.get_power_network_or_404(world, network_id)
    validate_power_consumer_exists(
        world,
        request.consumer_type,
        request.consumer_id,
    )

    power_network.add_consumer(request.consumer_type, request.consumer_id)
    return power_network.to_dict()


@router.delete(
    "/worlds/{world_id}/power-networks/{network_id}/consumers/{consumer_type}/{consumer_id}"
)
def remove_power_network_consumer(
    world_id: int,
    network_id: int,
    consumer_type: str,
    consumer_id: int,
):
    world = memory_store.get_world_or_404(world_id)
    power_network = memory_store.get_power_network_or_404(world, network_id)
    validate_power_consumer_type(consumer_type)

    if not network_has_consumer(power_network, consumer_type, consumer_id):
        raise HTTPException(status_code=404, detail="Power network consumer not found")

    power_network.remove_consumer(consumer_type, consumer_id)
    return power_network.to_dict()
