from dataclasses import dataclass, field


@dataclass(frozen=True)
class PowerConsumerRef:
    consumer_type: str
    consumer_id: int

    def to_dict(self) -> dict:
        return {
            "consumer_type": self.consumer_type,
            "consumer_id": self.consumer_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PowerConsumerRef":
        return cls(
            consumer_type=data["consumer_type"],
            consumer_id=data["consumer_id"],
        )


@dataclass
class PowerNetwork:
    id: int
    name: str
    source_ids: list[int] = field(default_factory=list)
    consumers: list[PowerConsumerRef] = field(default_factory=list)

    def add_source(self, source_id: int) -> None:
        if source_id not in self.source_ids:
            self.source_ids.append(source_id)

    def remove_source(self, source_id: int) -> bool:
        if source_id not in self.source_ids:
            return False
        self.source_ids.remove(source_id)
        return True

    def add_consumer(self, consumer_type: str, consumer_id: int) -> None:
        consumer = PowerConsumerRef(
            consumer_type=consumer_type,
            consumer_id=consumer_id,
        )
        if consumer not in self.consumers:
            self.consumers.append(consumer)

    def remove_consumer(self, consumer_type: str, consumer_id: int) -> bool:
        consumer = PowerConsumerRef(
            consumer_type=consumer_type,
            consumer_id=consumer_id,
        )
        if consumer not in self.consumers:
            return False
        self.consumers.remove(consumer)
        return True

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "source_ids": list(self.source_ids),
            "consumers": [
                consumer.to_dict()
                for consumer in self.consumers
            ],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PowerNetwork":
        return cls(
            id=data["id"],
            name=data["name"],
            source_ids=list(data.get("source_ids", [])),
            consumers=[
                PowerConsumerRef.from_dict(item) if isinstance(item, dict) else item
                for item in data.get("consumers", [])
            ],
        )
