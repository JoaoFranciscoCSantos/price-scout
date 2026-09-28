"""Parser de scraping genérico, configurável por seletor CSS.

Cobre a maioria das lojas simples: o preço está num elemento HTML
identificável por uma classe ou id fixo. Sites que precisem de
JavaScript para carregar o preço (ex: React/Vue client-side) vão
precisar de um parser à parte com Selenium — este aqui basta para
páginas estáticas.
"""

import re

import requests
from bs4 import BeautifulSoup

from models import CURRENCY_SYMBOLS, Price
from sites.base import PriceFetchError, SiteParser

# Aceita "599,99€", "599.99 €", "€599.99", "1.234,56€", etc.
_PRICE_RE = re.compile(r"[\d.,]+")



def _parse_price_text(text: str) -> float:
    """Converte texto de preço (com símbolo de moeda e separadores) em float."""
    match = _PRICE_RE.search(text)
    if not match:
        raise PriceFetchError(f"Não encontrei um número de preço em: {text!r}")

    raw = match.group()
    # Normaliza formato PT (1.234,56) e formato EN (1,234.56) para float
    if "," in raw and "." in raw:
        if raw.rfind(",") > raw.rfind("."):
            raw = raw.replace(".", "").replace(",", ".")
        else:
            raw = raw.replace(",", "")
    elif "," in raw:
        raw = raw.replace(",", ".")

    try:
        return float(raw)
    except ValueError as exc:
        raise PriceFetchError(f"Não consegui converter para número: {raw!r}") from exc

_CODE_RE = re.compile(r"(?<![A-Za-z])(EUR|GBP|USD)(?![A-Za-z])", re.IGNORECASE)

def _detect_currency(text: str) -> str | None:
    """Tenta descobrir a moeda pelo código (EUR, USD...) ou pelo símbolo (€, £, $)."""
    code = _CODE_RE.search(text)
    if code:
        return code.group(1).upper()
    for symbol, currency in CURRENCY_SYMBOLS.items():
        if symbol in text:
            return currency
    return None


class GenericScraperParser(SiteParser):
    """Faz scraping de uma página e extrai o preço de um elemento via seletor CSS."""

    def __init__(
        self,
        name: str,
        price_selector: str,
        currency: str | None = None,
        headers: dict | None = None,
    ):
        self.name = name
        self.price_selector = price_selector
        self.currency = currency  # se None, deteta pelo texto do preço
        self.headers = headers or {"User-Agent": "Mozilla/5.0 (price-scout)"}

    def get_price(self, url: str) -> Price:
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
        except requests.RequestException as exc:
            raise PriceFetchError(f"Falha ao aceder a {url}: {exc}") from exc

        soup = BeautifulSoup(response.text, "html.parser")
        element = soup.select_one(self.price_selector)
        if element is None:
            raise PriceFetchError(
                f"Seletor {self.price_selector!r} não encontrado em {url}"
            )

        text = element.get_text()
        amount = _parse_price_text(text)
        currency = self.currency or _detect_currency(text) or "EUR"
        return Price(amount, currency)