from dataclasses import dataclass, field

from app.engine.definitions.factory_level_definition import FactoryLevelDefinition
from app.engine.definitions.machine_definition import MachineDefinition
from app.engine.definitions.module_definition import ModuleDefinition
from app.engine.definitions.producer_definition import ProducerDefinition
from app.engine.definitions.recipe_definition import Recipe
from app.engine.definitions.resource_node_definition import ResourceNodeDefinition
from app.engine.definitions.su_source_definition import SUSourceDefinition


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
    from app.engine.content.loader import load_game_definitions_from_template

    return load_game_definitions_from_template("default")
