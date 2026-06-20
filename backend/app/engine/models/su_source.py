from dataclasses import dataclass


@dataclass
class SUSource:
    id: int
    name: str
    su_output: int

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "su_output": self.su_output,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SUSource":
        return cls(
            id=data["id"],
            name=data["name"],
            su_output=data["su_output"],
        )
