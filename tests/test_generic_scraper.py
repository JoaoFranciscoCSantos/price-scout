"""Testes do parsing de texto de preços (formatos PT e EN)."""

import pytest

from sites.base import PriceFetchError
from sites.generic_scraper import _parse_price_text


@pytest.mark.parametrize(
    "text, expected",
    [
        ("599,99€", 599.99),
        ("€599.99", 599.99),
        ("1.234,56€", 1234.56),
        ("1,234.56", 1234.56),
        ("  42€  ", 42.0),
        ("42", 42.0),
    ],
)
def test_parse_price_text_valid(text, expected):
    assert _parse_price_text(text) == expected


def test_parse_price_text_sem_numero_levanta_erro():
    with pytest.raises(PriceFetchError):
        _parse_price_text("Esgotado")
