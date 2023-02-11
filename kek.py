from dataclasses import dataclass, fields


@dataclass
class FilmInformation:
    budget: list[str]
    # rating: str
    # description: str
    # penis: bool
    # active: bool = True

kek = fields(FilmInformation)
print(kek)
print(kek[0])
print(kek[0].type == list)
