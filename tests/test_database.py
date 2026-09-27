"""Testes da camada de base de dados. Cada teste usa uma BD SQLite temporária
(fixture tmp_path do pytest), para nunca tocar em price_scout.db real."""

from datetime import datetime, timedelta

from database import add_price_entry, get_connection, get_latest_prices, get_or_create_item, get_price_history
from models import PriceEntry


def test_get_or_create_item_e_idempotente(tmp_path):
    conn = get_connection(tmp_path / "test.db")

    item1 = conn and get_or_create_item(conn, "RTX 4070")
    item2 = get_or_create_item(conn, "RTX 4070")

    assert item1.id == item2.id
    assert item1.name == "RTX 4070"


def test_get_latest_prices_ordena_por_preco_ascendente(tmp_path):
    conn = get_connection(tmp_path / "test.db")
    item = get_or_create_item(conn, "RTX 4070")

    add_price_entry(conn, PriceEntry(item_id=item.id, site="SiteCaro", price=599.99, url="http://a"))
    add_price_entry(conn, PriceEntry(item_id=item.id, site="SiteBarato", price=549.99, url="http://b"))

    rows = get_latest_prices(conn, item.id)

    assert [r["site"] for r in rows] == ["SiteBarato", "SiteCaro"]


def test_get_latest_prices_so_devolve_a_leitura_mais_recente_por_site(tmp_path):
    conn = get_connection(tmp_path / "test.db")
    item = get_or_create_item(conn, "RTX 4070")

    ontem = datetime.now() - timedelta(days=1)
    add_price_entry(conn, PriceEntry(item_id=item.id, site="SiteA", price=599.99, url="http://a", timestamp=ontem))
    add_price_entry(conn, PriceEntry(item_id=item.id, site="SiteA", price=549.99, url="http://a"))

    rows = get_latest_prices(conn, item.id)

    assert len(rows) == 1
    assert rows[0]["price"] == 549.99


def test_get_price_history_mantem_todas_as_leituras(tmp_path):
    conn = get_connection(tmp_path / "test.db")
    item = get_or_create_item(conn, "RTX 4070")

    add_price_entry(conn, PriceEntry(item_id=item.id, site="SiteA", price=599.99, url="http://a"))
    add_price_entry(conn, PriceEntry(item_id=item.id, site="SiteA", price=549.99, url="http://a"))

    history = get_price_history(conn, item.id, site="SiteA")

    assert len(history) == 2
