from dataclasses import dataclass, field

from app.engine.inventory.entity_stack import EntityStack


@dataclass
class Inventory:
    normal_items: dict[str, int] = field(default_factory=dict)
    entity_items: list[EntityStack] = field(default_factory=list)

    def add_normal_item(self, item_id: str, amount: int) -> None:
        if amount <= 0:
            return
        self.normal_items[item_id] = self.get_normal_amount(item_id) + amount

    def remove_normal_item(self, item_id: str, amount: int) -> bool:
        if amount <= 0 or self.get_normal_amount(item_id) < amount:
            return False

        remaining_amount = self.get_normal_amount(item_id) - amount
        if remaining_amount <= 0:
            self.normal_items.pop(item_id, None)
        else:
            self.normal_items[item_id] = remaining_amount
        return True

    def get_normal_amount(self, item_id: str) -> int:
        return self.normal_items.get(item_id, 0)

    def has_normal_items(self, item_id: str, amount: int) -> bool:
        return self.get_normal_amount(item_id) >= amount

    def add_entity_stack(self, stack: EntityStack) -> None:
        if stack.amount <= 0:
            return

        for existing_stack in self.entity_items:
            if _entity_stack_key(existing_stack) == _entity_stack_key(stack):
                existing_stack.amount += stack.amount
                return

        self.entity_items.append(stack)

    def remove_entity_stack(
        self,
        object_id: str,
        entity_type: str,
        amount: int = 1,
        entity_data: dict | None = None,
    ) -> bool:
        stack = self.find_entity_stack(object_id, entity_type, entity_data)
        if stack is None:
            return False

        if amount <= 0:
            return False

        if stack.amount < amount:
            return False

        stack.amount -= amount
        if stack.amount <= 0:
            self.entity_items.remove(stack)
        return True

    def find_entity_stack(
        self,
        object_id: str,
        entity_type: str,
        entity_data: dict | None = None,
    ) -> EntityStack | None:
        target_data = None
        if entity_data is not None:
            target_data = _freeze_entity_data(entity_data)

        for stack in self.entity_items:
            if stack.object_id != object_id or stack.entity_type != entity_type:
                continue
            if target_data is not None and _freeze_entity_data(stack.entity_data) != target_data:
                continue
            return stack

        return None

    def to_dict(self) -> dict:
        return {
            "normal_items": dict(self.normal_items),
            "entity_items": [
                stack.to_dict()
                for stack in self.entity_items
            ],
        }

    @classmethod
    def from_dict(cls, data) -> "Inventory":
        if isinstance(data, Inventory):
            return data

        return cls(
            normal_items=dict(data.get("normal_items", {})),
            entity_items=[
                EntityStack.from_dict(item) if isinstance(item, dict) else item
                for item in data.get("entity_items", [])
            ],
        )

    def __eq__(self, other) -> bool:
        if isinstance(other, Inventory):
            return (
                self.normal_items == other.normal_items
                and [
                    stack.to_dict()
                    for stack in self.entity_items
                ]
                == [
                    stack.to_dict()
                    for stack in other.entity_items
                ]
            )
        return False


def _entity_stack_key(stack: EntityStack) -> tuple:
    return (
        stack.object_id,
        stack.entity_type,
        _freeze_entity_data(stack.entity_data),
    )


def _freeze_entity_data(data: dict) -> tuple:
    return tuple(
        (key, _freeze_value(value))
        for key, value in sorted(data.items())
    )


def _freeze_value(value):
    if isinstance(value, dict):
        return _freeze_entity_data(value)
    if isinstance(value, list):
        return tuple(_freeze_value(item) for item in value)
    return value
