from dataclasses import dataclass, field


@dataclass
class Recipe:
    id: str
    name: str

    required_machines: list[str]
    duration: float
    input_items: dict[str, int] = field(default_factory=dict)
    output_items: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "required_machines": list(self.required_machines),
            "input_items": dict(self.input_items),
            "output_items": dict(self.output_items),
            "duration": self.duration,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Recipe":
        return cls(
            id=data["id"],
            name=data["name"],
            required_machines=list(data.get("required_machines", [])),
            input_items=dict(data.get("input_items", {})),
            output_items=dict(data.get("output_items", {})),
            duration=data["duration"],
        )

    def requires_machine(self, machine_id: str) -> bool:
        return machine_id in self.required_machines

    def get_input_amount(self, item_id: str) -> int:
        return self.input_items.get(item_id, 0)

    def get_output_amount(self, item_id: str) -> int:
        return self.output_items.get(item_id, 0)


def recipe_exists(recipe_id: str) -> bool:
    from app.engine.content.recipe_definitions import RECIPES

    return recipe_id in RECIPES


def get_recipe(recipe_id: str) -> Recipe | None:
    from app.engine.content.recipe_definitions import RECIPES

    return RECIPES.get(recipe_id)


def __getattr__(name: str):
    if name == "RECIPES":
        from app.engine.content.recipe_definitions import RECIPES

        return RECIPES

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
