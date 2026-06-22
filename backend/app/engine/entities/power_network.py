from dataclasses import dataclass, field


@dataclass(frozen=True)
class PowerSourceRef:
    source_type: str
    source_id: int

    def to_dict(self) -> dict:
        return {
            "source_type": self.source_type,
            "source_id": self.source_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PowerSourceRef":
        return cls(
            source_type=data["source_type"],
            source_id=data["source_id"],
        )


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
    sources: list[PowerSourceRef] = field(default_factory=list)
    consumers: list[PowerConsumerRef] = field(default_factory=list)

    def add_source(self, source_id: int, source_type: str = "su_source") -> None:
        source = PowerSourceRef(
            source_type=source_type,
            source_id=source_id,
        )
        if source not in self.sources:
            self.sources.append(source)

    def remove_source(self, source_id: int, source_type: str = "su_source") -> bool:
        source = PowerSourceRef(
            source_type=source_type,
            source_id=source_id,
        )
        if source not in self.sources:
            return False
        self.sources.remove(source)
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
            "sources": [
                source.to_dict()
                for source in self.sources
            ],
            "consumers": [
                consumer.to_dict()
                for consumer in self.consumers
            ],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PowerNetwork":
        sources = [
            PowerSourceRef.from_dict(item) if isinstance(item, dict) else item
            for item in data.get("sources", [])
        ]
        if not sources:
            sources = [
                PowerSourceRef(source_type="su_source", source_id=source_id)
                for source_id in data.get("source_ids", [])
            ]

        return cls(
            id=data["id"],
            name=data["name"],
            sources=sources,
            consumers=[
                PowerConsumerRef.from_dict(item) if isinstance(item, dict) else item
                for item in data.get("consumers", [])
            ],
        )
