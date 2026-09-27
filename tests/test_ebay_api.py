"""Testes do EbayApiParser. Usa monkeypatch para simular as respostas da API
do eBay — nunca faz chamadas de rede reais nem precisa de credenciais válidas."""

import pytest

from sites.base import PriceFetchError
from sites.ebay_api import EbayApiParser, _extract_legacy_item_id


@pytest.mark.parametrize(
    "url, expected_id",
    [
        ("https://www.ebay.com/itm/1234567890", "1234567890"),
        ("https://www.ebay.com/itm/Some-Product-Name/1234567890", "1234567890"),
        ("https://www.ebay.com/itm/1234567890?hash=abc", "1234567890"),
    ],
)
def test_extract_legacy_item_id_valido(url, expected_id):
    assert _extract_legacy_item_id(url) == expected_id


def test_extract_legacy_item_id_invalido_levanta_erro():
    with pytest.raises(PriceFetchError):
        _extract_legacy_item_id("https://www.ebay.com/sch/i.html?_nkw=teste")


class _FakeResponse:
    def __init__(self, json_data, status_code=200):
        self._json_data = json_data
        self.status_code = status_code

    def raise_for_status(self):
        pass

    def json(self):
        return self._json_data


def test_get_price_sucesso(monkeypatch):
    parser = EbayApiParser(client_id="fake-id", client_secret="fake-secret")

    def fake_post(url, **kwargs):
        return _FakeResponse({"access_token": "fake-token", "expires_in": 7200})

    def fake_get(url, **kwargs):
        assert kwargs["headers"]["Authorization"] == "Bearer fake-token"
        return _FakeResponse({"price": {"value": "129.99", "currency": "EUR"}})

    monkeypatch.setattr("requests.post", fake_post)
    monkeypatch.setattr("requests.get", fake_get)

    price = parser.get_price("https://www.ebay.com/itm/1234567890")

    assert price == 129.99


def test_get_price_reutiliza_token_em_chamadas_seguidas(monkeypatch):
    parser = EbayApiParser(client_id="fake-id", client_secret="fake-secret")
    calls = {"post": 0}

    def fake_post(url, **kwargs):
        calls["post"] += 1
        return _FakeResponse({"access_token": "fake-token", "expires_in": 7200})

    def fake_get(url, **kwargs):
        return _FakeResponse({"price": {"value": "50.00", "currency": "EUR"}})

    monkeypatch.setattr("requests.post", fake_post)
    monkeypatch.setattr("requests.get", fake_get)

    parser.get_price("https://www.ebay.com/itm/111")
    parser.get_price("https://www.ebay.com/itm/222")

    assert calls["post"] == 1  # só pediu token uma vez, reutilizou na 2ª chamada


def test_get_price_resposta_sem_preco_levanta_erro(monkeypatch):
    parser = EbayApiParser(client_id="fake-id", client_secret="fake-secret")

    monkeypatch.setattr(
        "requests.post", lambda url, **kwargs: _FakeResponse({"access_token": "t", "expires_in": 7200})
    )
    monkeypatch.setattr("requests.get", lambda url, **kwargs: _FakeResponse({"errors": ["not found"]}))

    with pytest.raises(PriceFetchError):
        parser.get_price("https://www.ebay.com/itm/999")
