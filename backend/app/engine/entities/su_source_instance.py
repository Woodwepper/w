from dataclasses import dataclass


@dataclass
class SUSourceInstance:
    id: int
    source_type: str
    name: str
    x: int = 0
    y: int = 0
    enabled: bool = True
    status: str = "active"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "source_type": self.source_type,
            "name": self.name,
            "x": self.x,
            "y": self.y,
            "enabled": self.enabled,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SUSourceInstance":
        return cls(
            id=data["id"],
            source_type=data["source_type"],
            name=data["name"],
            x=data.get("x", 0),
            y=data.get("y", 0),
            enabled=data.get("enabled", True),
            status=data.get("status", "active"),
        )
