"""Ponto de entrada do price-scout.

Lê `items.json`, corre o parser correto para cada site de cada item,
grava cada leitura no histórico (SQLite) e no fim mostra um resumo
com o site mais barato por item.

Uso:
    python main.py
"""

import json
from pathlib import Path

from database import add_price_entry, get_connection, get_latest_prices, get_or_create_item
from models import PriceEntry
from sites.base import PriceFetchError, SiteParser
from sites.generic_scraper import GenericScraperParser

CONFIG_PATH = Path(__file__).parent / "items.json"


def build_parser(site_config: dict) -> SiteParser:
    """Escolhe e configura o parser certo consoante o 'type' no items.json."""
    site_type = site_config["type"]

    if site_type == "scraper":
        return GenericScraperParser(
            name=site_config["site"],
            price_selector=site_config["price_selector"],
        )

    # Espaço reservado para quando adicionarmos parsers de API oficial:
    # if site_type == "api":
    #     return SomeApiParser(...)

    raise ValueError(f"Tipo de site desconhecido: {site_type!r}")


def load_config(path: Path = CONFIG_PATH) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def track_item(conn, item_config: dict) -> None:
    """Corre todos os sites configurados para um item e grava os preços."""
    item = get_or_create_item(conn, item_config["name"])
    print(f"\n{item.name}")

    for site_config in item_config["sites"]:
        parser = build_parser(site_config)
        url = site_config["url"]

        try:
            price = parser.get_price(url)
        except PriceFetchError as exc:
            print(f"  [!] {site_config['site']}: falhou ({exc})")
            continue

        add_price_entry(conn, PriceEntry(item_id=item.id, site=site_config["site"], price=price, url=url))
        print(f"  {site_config['site']}: {price:.2f}€")


def print_summary(conn, item_config: dict) -> None:
    """Mostra o site mais barato atual para este item."""
    item = get_or_create_item(conn, item_config["name"])
    rows = get_latest_prices(conn, item.id)
    if not rows:
        return

    best = rows[0]
    print(f"  -> Mais barato: {best['site']} a {best['price']:.2f}€")


def main() -> None:
    config = load_config()
    conn = get_connection()

    for item_config in config["items"]:
        track_item(conn, item_config)
        print_summary(conn, item_config)


if __name__ == "__main__":
    main()