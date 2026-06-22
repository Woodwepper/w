from dataclasses import dataclass, field

from app.engine.definitions.factory_level_definitions import FACTORY_LEVEL_DEFINITIONS
from app.engine.definitions.machine_definitions import MACHINE_DEFINITIONS
from app.engine.definitions.module_definitions import MODULE_DEFINITIONS
from app.engine.definitions.producer_definitions import PRODUCER_DEFINITIONS
from app.engine.definitions.recipe_definitions import RECIPES
from app.engine.definitions.resource_node_definitions import RESOURCE_NODE_DEFINITIONS
from app.engine.definitions.su_source_definitions import SU_SOURCE_DEFINITIONS
from app.engine.models.factory_level_definition import FactoryLevelDefinition
from app.engine.models.machine_definition import MachineDefinition
from app.engine.models.module_definition import ModuleDefinition
from app.engine.models.producer_definition import ProducerDefinition
from app.engine.models.producer_level_definition import ProducerLevelDefinition
from app.engine.models.recipe import Recipe
from app.engine.models.resource_node_definition import ResourceNodeDefinition
from app.engine.models.su_source_definition import SUSourceDefinition


@dataclass
class GameDefinitions:
    machines: dict[str, MachineDefinition] = field(default_factory=dict)
    modules: dict[str, ModuleDefinition] = field(default_factory=dict)
    recipes: dict[str, Recipe] = field(default_factory=dict)
    su_sources: dict[str, SUSourceDefinition] = field(default_factory=dict)
    factory_levels: dict[int, FactoryLevelDefinition] = field(default_factory=dict)
    resource_nodes: dict[str, ResourceNodeDefinition] = field(default_factory=dict)
    producers: dict[str, ProducerDefinition] = field(default_factory=dict)

    def get_machine(self, machine_type: str) -> MachineDefinition | None:
        return self.machines.get(machine_type)

    def get_module(self, module_type: str) -> ModuleDefinition | None:
        return self.modules.get(module_type)

    def get_recipe(self, recipe_id: str) -> Recipe | None:
        return self.recipes.get(recipe_id)

    def get_su_source(self, source_type: str) -> SUSourceDefinition | None:
        return self.su_sources.get(source_type)

    def get_factory_level(self, level: int) -> FactoryLevelDefinition | None:
        return self.factory_levels.get(level)

    def get_resource_node_definition(
        self,
        node_type: str,
    ) -> ResourceNodeDefinition | None:
        return self.resource_nodes.get(node_type)

    def get_producer(self, producer_type: str) -> ProducerDefinition | None:
        return self.producers.get(producer_type)


def create_default_definitions() -> GameDefinitions:
    machines = {
        machine_id: MachineDefinition(
            id=machine.id,
            name=machine.name,
            su_cost=machine.su_cost,
            allowed_recipes=[
                recipe.id
                for recipe in RECIPES.values()
                if machine_id in recipe.required_machines
            ],
            build_cost=dict(machine.build_cost),
            upgrade_costs={
                level: dict(cost)
                for level, cost in machine.upgrade_costs.items()
            },
            speed_multipliers=dict(machine.speed_multipliers) or {1: 1.0},
            icon=machine.icon,
            visual_key=machine.visual_key,
        )
        for machine_id, machine in MACHINE_DEFINITIONS.items()
    }

    modules = {
        module_id: ModuleDefinition(
            id=module.id,
            name=module.name,
            allowed_recipes=list(module.allowed_recipes),
            allowed_machine_types=list(module.allowed_machine_types),
            icon=module.icon,
            visual_key=module.visual_key,
        )
        for module_id, module in MODULE_DEFINITIONS.items()
    }

    producers = {
        producer_id: ProducerDefinition(
            id=producer.id,
            name=producer.name,
            allowed_node_types=list(producer.allowed_node_types),
            allowed_machine_types=list(producer.allowed_machine_types),
            base_duration=producer.base_duration,
            base_output_amount=producer.base_output_amount,
            levels={
                level: ProducerLevelDefinition(
                    level=level_definition.level,
                    machine_slots=level_definition.machine_slots,
                    upgrade_cost=dict(level_definition.upgrade_cost),
                )
                for level, level_definition in producer.levels.items()
            },
            icon=producer.icon,
            visual_key=producer.visual_key,
        )
        for producer_id, producer in PRODUCER_DEFINITIONS.items()
    }

    return GameDefinitions(
        machines=machines,
        modules=modules,
        recipes=dict(RECIPES),
        su_sources=dict(SU_SOURCE_DEFINITIONS),
        factory_levels=dict(FACTORY_LEVEL_DEFINITIONS),
        resource_nodes=dict(RESOURCE_NODE_DEFINITIONS),
        producers=producers,
    )
