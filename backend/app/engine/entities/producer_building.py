from dataclasses import dataclass, field

from app.engine.entities.machine_instance import MachineInstance
from app.engine.core.statuses import ProducerStatus
from app.engine.definitions.game_definitions import GameDefinitions


@dataclass
class ProducerBuilding:
    id: int
    name: str
    producer_type: str
    resource_node_id: int
    x: int = 0
    y: int = 0
    level: int = 1
    installed_machines: list[MachineInstance] = field(default_factory=list)
    priority: int = 100
    output_items: dict[str, int] = field(default_factory=dict)
    status: ProducerStatus = ProducerStatus.IDLE

    def add_machine(self, machine: MachineInstance) -> None:
        self.installed_machines.append(machine)

    def remove_machine(self, machine_id: int) -> bool:
        machine = self.get_machine(machine_id)
        if machine is None:
            return False
        self.installed_machines.remove(machine)
        return True

    def get_machine(self, machine_id: int) -> MachineInstance | None:
        for machine in self.installed_machines:
            if machine.id == machine_id:
                return machine
        return None

    def get_machines_by_type(self, machine_type: str) -> list[MachineInstance]:
        return [
            machine
            for machine in self.installed_machines
            if machine.machine_type == machine_type
        ]

    def clear_all_machine_progress(self) -> None:
        for machine in self.installed_machines:
            machine.clear_progress()

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

    def can_level_up(
        self,
        definitions: GameDefinitions,
        inventory: dict[str, int],
    ) -> bool:
        producer_definition = definitions.get_producer(self.producer_type)
        if producer_definition is None:
            return False

        next_level_definition = producer_definition.get_level_definition(self.level + 1)
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
        producer_definition = definitions.get_producer(self.producer_type)
        if producer_definition is None:
            return False

        next_level_definition = producer_definition.get_level_definition(self.level + 1)
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

    def get_machine_slot_limit(self, definitions: GameDefinitions) -> int:
        producer_definition = definitions.get_producer(self.producer_type)
        if producer_definition is None:
            return 0

        level_definition = producer_definition.get_level_definition(self.level)
        if level_definition is None:
            return 0

        return level_definition.machine_slots

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "producer_type": self.producer_type,
            "resource_node_id": self.resource_node_id,
            "x": self.x,
            "y": self.y,
            "level": self.level,
            "installed_machines": [
                machine.to_dict()
                for machine in self.installed_machines
            ],
            "priority": self.priority,
            "output_items": dict(self.output_items),
            "status": self.status.value,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ProducerBuilding":
        return cls(
            id=data["id"],
            name=data["name"],
            producer_type=data["producer_type"],
            resource_node_id=data["resource_node_id"],
            x=data.get("x", 0),
            y=data.get("y", 0),
            level=data.get("level", 1),
            installed_machines=[
                MachineInstance.from_dict(item) if isinstance(item, dict) else item
                for item in data.get("installed_machines", [])
            ],
            priority=data.get("priority", 100),
            output_items=dict(data.get("output_items", {})),
            status=ProducerStatus(data.get("status", ProducerStatus.IDLE.value)),
        )
