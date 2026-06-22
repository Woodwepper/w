from dataclasses import dataclass, field

from app.engine.definitions.factory_level_definition import FactoryLevelDefinition
from app.engine.definitions.machine_definition import MachineDefinition
from app.engine.definitions.module_definition import ModuleDefinition
from app.engine.definitions.producer_definition import ProducerDefinition
from app.engine.definitions.recipe_definition import Recipe
from app.engine.definitions.resource_node_definition import ResourceNodeDefinition
from app.engine.definitions.su_producer_definition import SUProducerDefinition
from app.engine.definitions.su_source_definition import SUSourceDefinition
from app.engine.definitions.su_unit_definition import SUUnitDefinition


@dataclass
class GameDefinitions:
    machines: dict[str, MachineDefinition] = field(default_factory=dict)
    modules: dict[str, ModuleDefinition] = field(default_factory=dict)
    recipes: dict[str, Recipe] = field(default_factory=dict)
    su_sources: dict[str, SUSourceDefinition] = field(default_factory=dict)
    su_units: dict[str, SUUnitDefinition] = field(default_factory=dict)
    su_producers: dict[str, SUProducerDefinition] = field(default_factory=dict)
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

    def get_su_unit(self, unit_type: str) -> SUUnitDefinition | None:
        return self.su_units.get(unit_type)

    def get_su_producer(self, producer_type: str) -> SUProducerDefinition | None:
        return self.su_producers.get(producer_type)

    def get_factory_level(self, level: int) -> FactoryLevelDefinition | None:
        return self.factory_levels.get(level)

    def get_resource_node_definition(
        self,
        node_type: str,
    ) -> ResourceNodeDefinition | None:
        return self.resource_nodes.get(node_type)

    def get_producer(self, producer_type: str) -> ProducerDefinition | None:
        return self.producers.get(producer_type)

    def to_dict(self) -> dict:
        return {
            "machines": {
                machine_id: machine.to_dict()
                for machine_id, machine in self.machines.items()
            },
            "modules": {
                module_id: module.to_dict()
                for module_id, module in self.modules.items()
            },
            "recipes": {
                recipe_id: recipe.to_dict()
                for recipe_id, recipe in self.recipes.items()
            },
            "su_sources": {
                source_id: su_source.to_dict()
                for source_id, su_source in self.su_sources.items()
            },
            "su_units": {
                unit_id: su_unit.to_dict()
                for unit_id, su_unit in self.su_units.items()
            },
            "su_producers": {
                producer_id: su_producer.to_dict()
                for producer_id, su_producer in self.su_producers.items()
            },
            "factory_levels": {
                level: factory_level.to_dict()
                for level, factory_level in self.factory_levels.items()
            },
            "resource_nodes": {
                node_id: resource_node.to_dict()
                for node_id, resource_node in self.resource_nodes.items()
            },
            "producers": {
                producer_id: producer.to_dict()
                for producer_id, producer in self.producers.items()
            },
        }

    @classmethod
    def from_dict(cls, data: dict) -> "GameDefinitions":
        return cls(
            machines={
                machine_id: MachineDefinition.from_dict(machine)
                for machine_id, machine in data.get("machines", {}).items()
            },
            modules={
                module_id: ModuleDefinition.from_dict(module)
                for module_id, module in data.get("modules", {}).items()
            },
            recipes={
                recipe_id: Recipe.from_dict(recipe)
                for recipe_id, recipe in data.get("recipes", {}).items()
            },
            su_sources={
                source_id: SUSourceDefinition.from_dict(su_source)
                for source_id, su_source in data.get("su_sources", {}).items()
            },
            su_units={
                unit_id: SUUnitDefinition.from_dict(su_unit)
                for unit_id, su_unit in data.get("su_units", {}).items()
            },
            su_producers={
                producer_id: SUProducerDefinition.from_dict(su_producer)
                for producer_id, su_producer in data.get("su_producers", {}).items()
            },
            factory_levels={
                int(level): FactoryLevelDefinition.from_dict(factory_level)
                for level, factory_level in data.get("factory_levels", {}).items()
            },
            resource_nodes={
                node_id: ResourceNodeDefinition.from_dict(resource_node)
                for node_id, resource_node in data.get("resource_nodes", {}).items()
            },
            producers={
                producer_id: ProducerDefinition.from_dict(producer)
                for producer_id, producer in data.get("producers", {}).items()
            },
        )


def create_default_definitions() -> GameDefinitions:
    from app.engine.content.loader import load_game_definitions_from_template

    return load_game_definitions_from_template("default")
