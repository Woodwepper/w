from pydantic import BaseModel, Field


class CreateWorldRequest(BaseModel):
    name: str = Field(default="New World")


class TickRequest(BaseModel):
    seconds: float


class AddInventoryItemRequest(BaseModel):
    item_id: str
    amount: int


class BuildInventoryMachineRequest(BaseModel):
    machine_type: str
    level: int = 1
    metadata: dict = Field(default_factory=dict)


class CreateFactoryRequest(BaseModel):
    name: str
    x: int = 0
    y: int = 0
    icon: str = "factory"
    visual_theme: str = "andesite"
    priority: int = 100


class UpdateFactoryRequest(BaseModel):
    name: str | None = None
    icon: str | None = None
    visual_theme: str | None = None
    priority: int | None = None


class AddFactoryInputRequest(BaseModel):
    item_id: str
    amount: int


class CollectOutputRequest(BaseModel):
    item_id: str
    amount: int


class CreateModuleRequest(BaseModel):
    module_type: str
    active_recipe: str | None = None


class SetModuleRecipeRequest(BaseModel):
    recipe_id: str


class BuildInstallMachineRequest(BaseModel):
    machine_type: str
    level: int = 1
    metadata: dict = Field(default_factory=dict)


class UpgradeMachineRequest(BaseModel):
    target_level: int


class CreateSUSourceRequest(BaseModel):
    source_type: str
    name: str
    x: int = 0
    y: int = 0


class CreatePowerNetworkRequest(BaseModel):
    name: str


class AddNetworkSourceRequest(BaseModel):
    source_id: int
    source_type: str = "su_source"


class AddNetworkConsumerRequest(BaseModel):
    consumer_type: str
    consumer_id: int


class CreateResourceNodeRequest(BaseModel):
    node_type: str
    name: str
    x: int
    y: int
    richness: int = 1
    hardness: float = 1.0
    required_machine_level: int = 1
    remaining_amount: int | None = None
    infinite: bool = False
    traits: list[str] = Field(default_factory=list)


class CreateProducerRequest(BaseModel):
    producer_type: str
    name: str
    resource_node_id: int
    level: int = 1
    priority: int = 100


class CollectProducerOutputRequest(BaseModel):
    item_id: str
    amount: int


class CreateSUProducerRequest(BaseModel):
    producer_type: str
    name: str
    x: int = 0
    y: int = 0
    level: int = 1
    enabled: bool = True


class AddSUProducerUnitRequest(BaseModel):
    unit_type: str
    amount: int = 1


class AddSUProducerInputRequest(BaseModel):
    item_id: str
    amount: int
