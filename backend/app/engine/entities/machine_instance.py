from dataclasses import dataclass, field
from typing import Any

from app.engine.core.statuses import FactoryStatus


@dataclass
class MachineInstance:
    id: int
    machine_type: str
    level: int = 1
    progress: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
    status: FactoryStatus = FactoryStatus.IDLE

    def clear_progress(self) -> None:
        self.progress = 0.0

    def set_level(self, level: int) -> None:
        self.level = max(1, level)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "machine_type": self.machine_type,
            "level": self.level,
            "progress": self.progress,
            "metadata": dict(self.metadata),
            "status": self.status.value,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MachineInstance":
        return cls(
            id=data["id"],
            machine_type=data["machine_type"],
            level=max(1, data.get("level", 1)),
            progress=data.get("progress", 0.0),
            metadata=dict(data.get("metadata", {})),
            status=FactoryStatus(data.get("status", FactoryStatus.IDLE.value)),
        )
