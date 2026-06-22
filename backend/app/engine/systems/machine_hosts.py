from collections.abc import Callable
from typing import Any

from app.engine.definitions.game_definitions import GameDefinitions
from app.engine.entities.machine_instance import MachineInstance


def can_install_machine_on_host(
    *,
    machine: MachineInstance | None,
    definitions: GameDefinitions,
    allowed_machine_types: list[str],
    installed_machines: list[MachineInstance],
    slot_limit: int,
    get_existing_machine: Callable[[int], MachineInstance | None],
) -> bool:
    if machine is None:
        return False

    machine_definition = definitions.get_machine(machine.machine_type)
    if machine_definition is None:
        return False

    if machine.machine_type not in allowed_machine_types:
        return False

    if get_existing_machine(machine.id) is not None:
        return False

    if len(installed_machines) >= slot_limit:
        return False

    return True


def create_machine_instance(
    machine_type: str,
    machine_id: int,
    level: int = 1,
    metadata: dict[str, Any] | None = None,
) -> MachineInstance:
    return MachineInstance(
        id=machine_id,
        machine_type=machine_type,
        level=max(1, level),
        metadata=dict(metadata or {}),
    )
