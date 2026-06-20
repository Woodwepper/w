from dataclasses import dataclass, field

from .producer_status import ProducerStatus


@dataclass
class ProducerBuilding:
    id: int
    name: str
    producer_type: str
    resource_node_id: int
    x: int = 0
    y: int = 0
    machine_level: int = 1
    efficiency_level: int = 1
    priority: int = 100
    progress: float = 0.0
    output_items: dict[str, int] = field(default_factory=dict)
    status: ProducerStatus = ProducerStatus.IDLE

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

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "producer_type": self.producer_type,
            "resource_node_id": self.resource_node_id,
            "x": self.x,
            "y": self.y,
            "machine_level": self.machine_level,
            "efficiency_level": self.efficiency_level,
            "priority": self.priority,
            "progress": self.progress,
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
            machine_level=data.get("machine_level", 1),
            efficiency_level=data.get("efficiency_level", 1),
            priority=data.get("priority", 100),
            progress=data.get("progress", 0.0),
            output_items=dict(data.get("output_items", {})),
            status=ProducerStatus(data.get("status", ProducerStatus.IDLE.value)),
        )
