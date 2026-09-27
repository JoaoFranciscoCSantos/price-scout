"""Interface comum a todos os parsers de sites.

Cada site (scraping ou API) implementa esta classe. O resto da aplicação
(main.py) só conhece esta interface — não sabe nem quer saber se por trás
está BeautifulSoup, Selenium ou uma chamada a uma API oficial.
"""

from abc import ABC, abstractmethod


class PriceFetchError(Exception):
    """Erro ao obter o preço de um site (página mudou, item esgotado, etc.)."""


class SiteParser(ABC):
    """Contrato que cada site deve implementar."""

    #: Nome do site, usado como identificador na base de dados (ex: "amazon")
    name: str = "base"

    @abstractmethod
    def get_price(self, url: str) -> float:
        """Devolve o preço atual do item nesse URL.

        Deve lançar PriceFetchError se não conseguir obter um preço válido
        (em vez de devolver None ou 0, para não poluir o histórico com
        valores errados).
        """
        raise NotImplementedError