from dataclasses import dataclass, field

from app.engine.entities.module_instance import ModuleInstance
from app.engine.core.statuses import FactoryStatus
from app.engine.definitions.factory_level_definition import FactoryLevelDefinition
from app.engine.definitions.game_definitions import GameDefinitions
from app.engine.inventory.inventory import Inventory


@dataclass
class FactoryBuilding:
    id: int
    name: str
    level: int = 1
    x: int = 0
    y: int = 0
    icon: str = "factory"
    visual_theme: str = "andesite"
    priority: int = 100
    modules: list[ModuleInstance] = field(default_factory=list)
    input_items: dict[str, int] = field(default_factory=dict)
    output_items: dict[str, int] = field(default_factory=dict)
    status: FactoryStatus = FactoryStatus.IDLE

    def add_input_item(self, item_id: str, amount: int) -> None:
        self.input_items[item_id] = self.get_input_amount(item_id) + amount

    def remove_input_item(self, item_id: str, amount: int) -> bool:
        current_amount = self.get_input_amount(item_id)
        if current_amount < amount:
            return False
        remaining_amount = current_amount - amount
        if remaining_amount <= 0:
            self.input_items.pop(item_id, None)
        else:
            self.input_items[item_id] = remaining_amount
        return True

    def get_input_amount(self, item_id: str) -> int:
        return self.input_items.get(item_id, 0)

    def has_input_item(self, item_id: str, amount: int) -> bool:
        return self.get_input_amount(item_id) >= amount

    def add_output_item(self, item_id: str, amount: int) -> None:
        self.output_items[item_id] = self.get_output_amount(item_id) + amount

    def remove_output_item(self, item_id: str, amount: int) -> bool:
        current_amount = self.get_output_amount(item_id)
        if current_amount < amount:
            return False
        remaining_amount = current_amount - amount
        if remaining_amount <= 0:
            self.output_items.pop(item_id, None)
        else:
            self.output_items[item_id] = remaining_amount
        return True

    def get_output_amount(self, item_id: str) -> int:
        return self.output_items.get(item_id, 0)

    def add_module(
        self,
        module: ModuleInstance,
        definitions: GameDefinitions,
    ) -> bool:
        if len(self.modules) >= self.get_module_slot_limit(definitions):
            return False

        self.modules.append(module)
        return True

    def remove_module(self, module_id: int) -> bool:
        module = self.get_module(module_id)
        if module is None:
            return False
        self.modules.remove(module)
        return True

    def get_module(self, module_id: int) -> ModuleInstance | None:
        for module in self.modules:
            if module.id == module_id:
                return module
        return None

    def get_modules_by_type(self, module_type: str) -> list[ModuleInstance]:
        return [
            module
            for module in self.modules
            if module.module_type == module_type
        ]

    def set_module_recipe(self, module_id: int, recipe_id: str | None) -> bool:
        module = self.get_module(module_id)
        if module is None:
            return False
        module.set_active_recipe(recipe_id)
        return True

    def can_level_up(
        self,
        definitions: GameDefinitions,
        inventory: Inventory,
    ) -> bool:
        next_level_definition = definitions.get_factory_level(self.level + 1)
        if next_level_definition is None:
            return False

        for item_id, amount in next_level_definition.upgrade_cost.items():
            if not inventory.has_normal_items(item_id, amount):
                return False

        return True

    def level_up(
        self,
        definitions: GameDefinitions,
        inventory: Inventory,
    ) -> bool:
        next_level_definition = definitions.get_factory_level(self.level + 1)
        if next_level_definition is None:
            return False

        if not self.can_level_up(definitions, inventory):
            return False

        for item_id, amount in next_level_definition.upgrade_cost.items():
            inventory.remove_normal_item(item_id, amount)

        self.level = next_level_definition.level
        return True

    def get_level_definition(
        self,
        definitions: GameDefinitions,
    ) -> FactoryLevelDefinition | None:
        return definitions.get_factory_level(self.level)

    def get_module_slot_limit(self, definitions: GameDefinitions) -> int:
        level_definition = self.get_level_definition(definitions)
        if level_definition is None:
            return 0
        return level_definition.module_slots

    def get_machine_slot_limit_per_module(self, definitions: GameDefinitions) -> int:
        level_definition = self.get_level_definition(definitions)
        if level_definition is None:
            return 0
        return level_definition.machine_slots_per_module

    def reset_status(self) -> None:
        self.status = FactoryStatus.IDLE

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "level": self.level,
            "x": self.x,
            "y": self.y,
            "icon": self.icon,
            "visual_theme": self.visual_theme,
            "priority": self.priority,
            "modules": [module.to_dict() for module in self.modules],
            "input_items": dict(self.input_items),
            "output_items": dict(self.output_items),
            "status": self.status.value,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "FactoryBuilding":
        return cls(
            id=data["id"],
            name=data["name"],
            level=data.get("level", 1),
            x=data.get("x", 0),
            y=data.get("y", 0),
            icon=data.get("icon", "factory"),
            visual_theme=data.get("visual_theme", "andesite"),
            priority=data.get("priority", 100),
            modules=[
                ModuleInstance.from_dict(item) if isinstance(item, dict) else item
                for item in data.get("modules", [])
            ],
            input_items=dict(data.get("input_items", {})),
            output_items=dict(data.get("output_items", {})),
            status=FactoryStatus(data.get("status", FactoryStatus.IDLE.value)),
        )
