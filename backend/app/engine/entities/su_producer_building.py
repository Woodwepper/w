from dataclasses import dataclass, field

from app.engine.core.statuses import SUProducerStatus
from app.engine.definitions.game_definitions import GameDefinitions


@dataclass
class SUProducerBuilding:
    id: int
    name: str
    producer_type: str
    x: int = 0
    y: int = 0
    level: int = 1
    installed_units: dict[str, int] = field(default_factory=dict)
    input_items: dict[str, int] = field(default_factory=dict)
    enabled: bool = True
    status: SUProducerStatus = SUProducerStatus.IDLE

    def add_unit(self, unit_type: str, amount: int = 1) -> None:
        if amount <= 0:
            return
        self.installed_units[unit_type] = self.get_unit_amount(unit_type) + amount

    def remove_unit(self, unit_type: str, amount: int = 1) -> bool:
        current_amount = self.get_unit_amount(unit_type)
        if amount <= 0 or current_amount < amount:
            return False

        remaining_amount = current_amount - amount
        if remaining_amount <= 0:
            self.installed_units.pop(unit_type, None)
        else:
            self.installed_units[unit_type] = remaining_amount
        return True

    def get_unit_amount(self, unit_type: str) -> int:
        return self.installed_units.get(unit_type, 0)

    def get_installed_unit_count(self) -> int:
        return sum(self.installed_units.values())

    def add_input_item(self, item_id: str, amount: int) -> None:
        if amount <= 0:
            return
        self.input_items[item_id] = self.get_input_amount(item_id) + amount

    def remove_input_item(self, item_id: str, amount: int) -> bool:
        current_amount = self.get_input_amount(item_id)
        if amount <= 0 or current_amount < amount:
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

    def get_unit_slot_limit(self, definitions: GameDefinitions) -> int:
        producer_definition = definitions.get_su_producer(self.producer_type)
        if producer_definition is None:
            return 0

        level_definition = producer_definition.get_level_definition(self.level)
        if level_definition is None:
            return 0

        return level_definition.unit_slots

    def can_level_up(
        self,
        definitions: GameDefinitions,
        inventory: dict[str, int],
    ) -> bool:
        producer_definition = definitions.get_su_producer(self.producer_type)
        if producer_definition is None:
            return False

        next_level_definition = producer_definition.get_level_definition(
            self.level + 1
        )
        if next_level_definition is None:
            return False

        for item_id, amount in next_level_definition.upgrade_cost.items():
            if inventory.get(item_id, 0) < amount:
                return False

        return True

    def level_up(
        self,
        definitions: GameDefinitions,
        inventory: dict[str, int],
    ) -> bool:
        producer_definition = definitions.get_su_producer(self.producer_type)
        if producer_definition is None:
            return False

        next_level_definition = producer_definition.get_level_definition(
            self.level + 1
        )
        if next_level_definition is None:
            return False

        if not self.can_level_up(definitions, inventory):
            return False

        for item_id, amount in next_level_definition.upgrade_cost.items():
            remaining_amount = inventory.get(item_id, 0) - amount
            if remaining_amount <= 0:
                inventory.pop(item_id, None)
            else:
                inventory[item_id] = remaining_amount

        self.level = next_level_definition.level
        return True

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "producer_type": self.producer_type,
            "x": self.x,
            "y": self.y,
            "level": self.level,
            "installed_units": dict(self.installed_units),
            "input_items": dict(self.input_items),
            "enabled": self.enabled,
            "status": self.status.value,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SUProducerBuilding":
        return cls(
            id=data["id"],
            name=data["name"],
            producer_type=data["producer_type"],
            x=data.get("x", 0),
            y=data.get("y", 0),
            level=data.get("level", 1),
            installed_units=dict(data.get("installed_units", {})),
            input_items=dict(data.get("input_items", {})),
            enabled=data.get("enabled", True),
            status=SUProducerStatus(
                data.get("status", SUProducerStatus.IDLE.value)
            ),
        )
