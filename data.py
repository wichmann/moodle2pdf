
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Section:
    id: int = 0
    name: str = ''

    def __str__(self):
        return '{} ({})'.format(self.name, self.id)
