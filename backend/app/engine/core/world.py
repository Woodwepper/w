from dataclasses import dataclass, field

from app.engine.entities.power_network import PowerNetwork
from app.engine.entities.factory_building import FactoryBuilding
from app.engine.entities.producer_building import ProducerBuilding
from app.engine.entities.resource_node import ResourceNode
from app.engine.entities.su_source import SUSource
from app.engine.entities.su_source_instance import SUSourceInstance
from app.engine.entities.su_producer_building import SUProducerBuilding
from app.engine.inventory.inventory import Inventory
from app.engine.definitions.game_definitions import (
    GameDefinitions,
    create_default_definitions,
)


@dataclass
class World:
    id: int
    name: str

    definitions: GameDefinitions = field(default_factory=create_default_definitions)
    simulated_time: float = 0.0

    inventory: Inventory = field(default_factory=Inventory)

    su_sources: list[SUSourceInstance] = field(default_factory=list)
    su_producers: list[SUProducerBuilding] = field(default_factory=list)
    power_networks: list[PowerNetwork] = field(default_factory=list)
    factories: list[FactoryBuilding] = field(default_factory=list)
    resource_nodes: list[ResourceNode] = field(default_factory=list)
    producers: list[ProducerBuilding] = field(default_factory=list)

    su_produced: int = 0
    su_required: int = 0
    su_available: int = 0

    def add_inventory_item(self, item_id: str, amount: int) -> None:
        self.inventory.add_normal_item(item_id, amount)

    def remove_inventory_item(self, item_id: str, amount: int) -> bool:
        return self.inventory.remove_normal_item(item_id, amount)

    def get_inventory_amount(self, item_id: str) -> int:
        return self.inventory.get_normal_amount(item_id)

    def has_inventory_item(self, item_id: str, amount: int) -> bool:
        return self.inventory.has_normal_items(item_id, amount)

    def add_factory(self, factory: FactoryBuilding) -> None:
        self.factories.append(factory)

    def get_factory(self, factory_id: int) -> FactoryBuilding | None:
        for factory in self.factories:
            if factory.id == factory_id:
                return factory
        return None

    def remove_factory(self, factory_id: int) -> bool:
        factory = self.get_factory(factory_id)
        if factory is None:
            return False
        self.factories.remove(factory)
        return True

    def add_su_source(self, su_source: SUSourceInstance) -> None:
        self.su_sources.append(su_source)

    def get_su_source(self, su_source_id: int) -> SUSourceInstance | None:
        for su_source in self.su_sources:
            if su_source.id == su_source_id:
                return su_source
        return None

    def remove_su_source(self, su_source_id: int) -> bool:
        su_source = self.get_su_source(su_source_id)
        if su_source is None:
            return False
        self.su_sources.remove(su_source)
        return True

    def add_su_producer(self, su_producer: SUProducerBuilding) -> None:
        self.su_producers.append(su_producer)

    def get_su_producer(self, su_producer_id: int) -> SUProducerBuilding | None:
        for su_producer in self.su_producers:
            if su_producer.id == su_producer_id:
                return su_producer
        return None

    def remove_su_producer(self, su_producer_id: int) -> bool:
        su_producer = self.get_su_producer(su_producer_id)
        if su_producer is None:
            return False
        self.su_producers.remove(su_producer)
        return True

    def add_power_network(self, power_network: PowerNetwork) -> None:
        self.power_networks.append(power_network)

    def get_power_network(self, power_network_id: int) -> PowerNetwork | None:
        for power_network in self.power_networks:
            if power_network.id == power_network_id:
                return power_network
        return None

    def remove_power_network(self, power_network_id: int) -> bool:
        power_network = self.get_power_network(power_network_id)
        if power_network is None:
            return False
        self.power_networks.remove(power_network)
        return True

    def add_resource_node(self, resource_node: ResourceNode) -> None:
        self.resource_nodes.append(resource_node)

    def get_resource_node(self, resource_node_id: int) -> ResourceNode | None:
        for resource_node in self.resource_nodes:
            if resource_node.id == resource_node_id:
                return resource_node
        return None

    def remove_resource_node(self, resource_node_id: int) -> bool:
        resource_node = self.get_resource_node(resource_node_id)
        if resource_node is None:
            return False
        self.resource_nodes.remove(resource_node)
        return True

    def add_producer(self, producer: ProducerBuilding) -> None:
        self.producers.append(producer)

    def get_producer(self, producer_id: int) -> ProducerBuilding | None:
        for producer in self.producers:
            if producer.id == producer_id:
                return producer
        return None

    def remove_producer(self, producer_id: int) -> bool:
        producer = self.get_producer(producer_id)
        if producer is None:
            return False
        self.producers.remove(producer)
        return True

    @classmethod
    def from_dict(cls, data: dict) -> "World":
        return cls(
            id=data["id"],
            name=data["name"],
            simulated_time=data.get("simulated_time", 0.0),
            inventory=Inventory.from_dict(data.get("inventory", {})),
            su_sources=[
                _su_source_from_dict(item) if isinstance(item, dict) else item
                for item in data.get("su_sources", [])
            ],
            su_producers=[
                SUProducerBuilding.from_dict(item) if isinstance(item, dict) else item
                for item in data.get("su_producers", [])
            ],
            power_networks=[
                PowerNetwork.from_dict(item) if isinstance(item, dict) else item
                for item in data.get("power_networks", [])
            ],
            factories=[
                FactoryBuilding.from_dict(item) if isinstance(item, dict) else item
                for item in data.get("factories", [])
            ],
            resource_nodes=[
                ResourceNode.from_dict(item) if isinstance(item, dict) else item
                for item in data.get("resource_nodes", [])
            ],
            producers=[
                ProducerBuilding.from_dict(item) if isinstance(item, dict) else item
                for item in data.get("producers", [])
            ],
            su_produced=data.get("su_produced", 0),
            su_required=data.get("su_required", data.get("su_requiered", 0)),
            su_available=data.get("su_available", 0),
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "simulated_time": self.simulated_time,
            "inventory": self.inventory.to_dict(),
            "su_sources": [s.to_dict() for s in self.su_sources],
            "su_producers": [p.to_dict() for p in self.su_producers],
            "power_networks": [p.to_dict() for p in self.power_networks],
            "factories": [f.to_dict() for f in self.factories],
            "resource_nodes": [r.to_dict() for r in self.resource_nodes],
            "producers": [p.to_dict() for p in self.producers],
            "su_produced": self.su_produced,
            "su_required": self.su_required,
            "su_available": self.su_available,
        }


def _su_source_from_dict(data: dict) -> SUSourceInstance | SUSource:
    if "source_type" in data:
        return SUSourceInstance.from_dict(data)
    return SUSource.from_dict(data)
