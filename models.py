"""Modelos de dados do price-scout.

Define as estruturas usadas em toda a aplicação para representar um item
seguido e cada leitura de preço recolhida num site.
"""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Item:
    """Um item que estamos a seguir (ex: 'Placa gráfica RTX 4070')."""

    name: str
    id: int | None = None  # None até ser inserido na base de dados

    def __str__(self) -> str:
        return self.name


@dataclass
class PriceEntry:
    """Uma leitura de preço de um item, num site, num determinado momento."""

    item_id: int
    site: str
    price: float
    url: str
    timestamp: datetime = field(default_factory=datetime.now)
    id: int | None = None

    def __str__(self) -> str:
        return f"{self.site}: {self.price:.2f}€ ({self.timestamp:%Y-%m-%d %H:%M})"