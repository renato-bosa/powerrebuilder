from dataclasses import dataclass


@dataclass
class PBSourcedEntity:
    name: str

    @property
    def qualified_name(self) -> str:
        return self.name 