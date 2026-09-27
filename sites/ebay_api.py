"""Parser via API oficial do eBay (Browse API).

Requer uma app registada em https://developer.ebay.com/my/keys (grátis).
As credenciais (EBAY_CLIENT_ID, EBAY_CLIENT_SECRET) devem vir de variáveis
de ambiente — nunca hardcoded nem commitadas no repositório.

Fluxo:
  1. Extrai o item ID (legacy) do URL do anúncio (ex: .../itm/1234567890)
  2. Pede um access token via OAuth client credentials (válido ~2h, cacheado)
  3. Chama get_item_by_legacy_id e lê o preço da resposta
"""

import re
import time

import requests

from sites.base import PriceFetchError, SiteParser

_TOKEN_URL = "https://api.ebay.com/identity/v1/oauth2/token"
_ITEM_URL = "https://api.ebay.com/buy/browse/v1/item/get_item_by_legacy_id"
_SCOPE = "https://api.ebay.com/oauth/api_scope"

# Aceita URLs como https://www.ebay.com/itm/1234567890 ou .../itm/nome-do-produto/1234567890
_ITEM_ID_RE = re.compile(r"/itm/(?:[^/]+/)?(\d+)")


def _extract_legacy_item_id(url: str) -> str:
    match = _ITEM_ID_RE.search(url)
    if not match:
        raise PriceFetchError(f"Não consegui extrair o item ID do URL do eBay: {url}")
    return match.group(1)


class EbayApiParser(SiteParser):
    """Obtém o preço de um anúncio do eBay via Browse API."""

    name = "ebay"

    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self._token: str | None = None
        self._token_expires_at: float = 0.0

    def _get_access_token(self) -> str:
        """Devolve um access token válido, pedindo um novo só quando o anterior expira."""
        if self._token and time.time() < self._token_expires_at:
            return self._token

        try:
            response = requests.post(
                _TOKEN_URL,
                auth=(self.client_id, self.client_secret),
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data={"grant_type": "client_credentials", "scope": _SCOPE},
                timeout=10,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise PriceFetchError(f"Falha ao autenticar na API do eBay: {exc}") from exc

        data = response.json()
        self._token = data["access_token"]
        # Guarda margem de segurança de 60s antes da expiração real
        self._token_expires_at = time.time() + data["expires_in"] - 60
        return self._token

    def get_price(self, url: str) -> float:
        item_id = _extract_legacy_item_id(url)
        token = self._get_access_token()

        try:
            response = requests.get(
                _ITEM_URL,
                params={"legacy_item_id": item_id},
                headers={"Authorization": f"Bearer {token}"},
                timeout=10,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise PriceFetchError(f"Falha ao consultar item {item_id} no eBay: {exc}") from exc

        data = response.json()
        try:
            return float(data["price"]["value"])
        except (KeyError, ValueError) as exc:
            raise PriceFetchError(f"Resposta do eBay sem preço válido para {item_id}: {data}") from exc
