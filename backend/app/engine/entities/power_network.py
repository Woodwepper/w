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
    su_producer_ids: list[int] = field(default_factory=list)
    consumers: list[PowerConsumerRef] = field(default_factory=list)

    def add_source(self, su_producer_id: int) -> None:
        if su_producer_id not in self.su_producer_ids:
            self.su_producer_ids.append(su_producer_id)

    def remove_source(self, su_producer_id: int) -> bool:
        if su_producer_id not in self.su_producer_ids:
            return False
        self.su_producer_ids.remove(su_producer_id)
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
            "su_producer_ids": list(self.su_producer_ids),
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
            su_producer_ids=list(data.get("su_producer_ids", [])),
            consumers=[
                PowerConsumerRef.from_dict(item) if isinstance(item, dict) else item
                for item in data.get("consumers", [])
            ],
        )
