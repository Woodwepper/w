from app.engine.core.statuses import SUProducerStatus
from app.engine.core.world import World
from app.engine.entities.su_producer_building import SUProducerBuilding


def calculate_su_producer_output(
    world: World,
    su_producer: SUProducerBuilding,
) -> int:
    if not su_producer.enabled:
        su_producer.status = SUProducerStatus.DISABLED
        return 0

    producer_definition = world.definitions.get_su_producer(
        su_producer.producer_type
    )
    if producer_definition is None:
        su_producer.status = SUProducerStatus.INVALID_DEFINITION
        return 0

    if su_producer.get_installed_unit_count() <= 0:
        su_producer.status = SUProducerStatus.MISSING_UNIT
        return 0

    if (
        su_producer.get_installed_unit_count()
        > su_producer.get_unit_slot_limit(world.definitions)
    ):
        su_producer.status = SUProducerStatus.INVALID_DEFINITION
        return 0

    total_output = 0

    for unit_type, amount in su_producer.installed_units.items():
        if amount <= 0:
            continue

        unit_definition = world.definitions.get_su_unit(unit_type)
        if (
            unit_definition is None
            or unit_type not in producer_definition.allowed_unit_types
        ):
            su_producer.status = SUProducerStatus.INVALID_DEFINITION
            return 0

        if not _has_required_inputs(su_producer, unit_definition.input_items, amount):
            su_producer.status = SUProducerStatus.MISSING_INPUT
            return 0

        total_output += unit_definition.su_output * amount

    if total_output <= 0:
        su_producer.status = SUProducerStatus.MISSING_UNIT
        return 0

    su_producer.status = SUProducerStatus.ACTIVE
    return total_output


def consume_su_producer_inputs(
    world: World,
    su_producer: SUProducerBuilding,
) -> bool:
    if su_producer.status != SUProducerStatus.ACTIVE:
        return False

    producer_definition = world.definitions.get_su_producer(
        su_producer.producer_type
    )
    if producer_definition is None:
        return False

    required_items: dict[str, int] = {}

    for unit_type, amount in su_producer.installed_units.items():
        if amount <= 0:
            continue

        unit_definition = world.definitions.get_su_unit(unit_type)
        if (
            unit_definition is None
            or unit_type not in producer_definition.allowed_unit_types
        ):
            return False

        for item_id, required_amount in unit_definition.input_items.items():
            required_items[item_id] = (
                required_items.get(item_id, 0) + required_amount * amount
            )

    for item_id, amount in required_items.items():
        if not su_producer.has_input_item(item_id, amount):
            su_producer.status = SUProducerStatus.MISSING_INPUT
            return False

    for item_id, amount in required_items.items():
        su_producer.remove_input_item(item_id, amount)

    return True


def process_su_producers(world: World) -> None:
    for su_producer in world.su_producers:
        consume_su_producer_inputs(world, su_producer)


def _has_required_inputs(
    su_producer: SUProducerBuilding,
    input_items: dict[str, int],
    amount: int,
) -> bool:
    for item_id, required_amount in input_items.items():
        if su_producer.get_input_amount(item_id) < required_amount * amount:
            return False

    return True
