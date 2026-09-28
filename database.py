"""Camada de acesso à base de dados do price-scout.

Usa SQLite puro (sem ORM), com duas tabelas:
  - items: um registo por item seguido
  - price_history: uma linha por cada leitura de preço (histórico completo)
"""

import sqlite3
from pathlib import Path

from models import Item, PriceEntry

DB_PATH = Path(__file__).parent / "price_scout.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS items (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS price_history (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id   INTEGER NOT NULL,
    site      TEXT NOT NULL,
    price     REAL NOT NULL,
    url       TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    currency  TEXT NOT NULL DEFAULT 'EUR',
    FOREIGN KEY (item_id) REFERENCES items (id)
);
"""

def _migrate(conn: sqlite3.Connection) -> None:
    """Adiciona colunas novas a bases de dados criadas por versões anteriores."""
    columns = {row["name"] for row in conn.execute("PRAGMA table_info(price_history)")}
    if "currency" not in columns:
        conn.execute("ALTER TABLE price_history ADD COLUMN currency TEXT NOT NULL DEFAULT 'EUR'")
        conn.commit()

def get_connection(db_path: Path = DB_PATH) -> sqlite3.Connection:
    """Abre uma ligação à base de dados, criando o schema se necessário."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    _migrate(conn)
    return conn


def get_or_create_item(conn: sqlite3.Connection, name: str) -> Item:
    """Devolve o Item com este nome, criando-o na base de dados se não existir."""
    cur = conn.execute("SELECT id, name FROM items WHERE name = ?", (name,))
    row = cur.fetchone()
    if row is not None:
        return Item(id=row["id"], name=row["name"])

    cur = conn.execute("INSERT INTO items (name) VALUES (?)", (name,))
    conn.commit()
    return Item(id=cur.lastrowid, name=name)


def add_price_entry(conn: sqlite3.Connection, entry: PriceEntry) -> PriceEntry:
    """Grava uma nova leitura de preço no histórico."""
    cur = conn.execute(
        """
        INSERT INTO price_history (item_id, site, price, url, timestamp, currency)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (entry.item_id, entry.site, entry.price, entry.url,
         entry.timestamp.isoformat(), entry.currency),
    )
    conn.commit()
    entry.id = cur.lastrowid
    return entry


def get_latest_prices(conn: sqlite3.Connection, item_id: int) -> list[sqlite3.Row]:
    """Devolve a leitura mais recente de cada site para este item."""
    return conn.execute(
        """
        SELECT ph.site, ph.price, ph.currency, ph.url, ph.timestamp
        FROM price_history ph
        INNER JOIN (
            SELECT site, MAX(timestamp) AS max_ts
            FROM price_history
            WHERE item_id = ?
            GROUP BY site
        ) latest
        ON ph.site = latest.site AND ph.timestamp = latest.max_ts
        WHERE ph.item_id = ?
        ORDER BY ph.price ASC
        """,
        (item_id, item_id),
    ).fetchall()


def get_price_history(conn: sqlite3.Connection, item_id: int, site: str | None = None) -> list[sqlite3.Row]:
    """Devolve o histórico completo de preços de um item (opcionalmente filtrado por site)."""
    if site is not None:
        return conn.execute(
            """
            SELECT site, price, currency, url, timestamp FROM price_history
            WHERE item_id = ? AND site = ?
            ORDER BY timestamp ASC
            """,
            (item_id, site),
        ).fetchall()

    return conn.execute(
        """
        SELECT site, price, currency, url, timestamp FROM price_history
        WHERE item_id = ?
        ORDER BY timestamp ASC
        """,
        (item_id,),
    ).fetchall()