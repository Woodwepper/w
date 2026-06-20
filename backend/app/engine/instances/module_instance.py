from dataclasses import dataclass, field

from app.engine.models.factory_status import FactoryStatus
from .machine_instance import MachineInstance


@dataclass
class ModuleInstance:
    id: int
    module_type: str
    active_recipe: str | None = None
    installed_machines: list[MachineInstance] = field(default_factory=list)
    status: FactoryStatus = FactoryStatus.IDLE

    def set_active_recipe(self, recipe_id: str | None) -> None:
        if self.active_recipe != recipe_id:
            self.active_recipe = recipe_id
            self.clear_all_machine_progress()

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

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "module_type": self.module_type,
            "active_recipe": self.active_recipe,
            "installed_machines": [
                machine.to_dict()
                for machine in self.installed_machines
            ],
            "status": self.status.value,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ModuleInstance":
        return cls(
            id=data["id"],
            module_type=data["module_type"],
            active_recipe=data.get("active_recipe"),
            installed_machines=[
                MachineInstance.from_dict(item) if isinstance(item, dict) else item
                for item in data.get("installed_machines", [])
            ],
            status=FactoryStatus(data.get("status", FactoryStatus.IDLE.value)),
        )
