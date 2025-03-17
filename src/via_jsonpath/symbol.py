from dataclasses import dataclass


@dataclass(frozen=True)
class Symbol:
    name: str

    def __str__(self):
        return self.name
