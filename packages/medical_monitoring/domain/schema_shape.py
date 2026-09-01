"""Stdlib-only SQLite schema shape extraction shared by R1 and R7.

The shape is deliberately limited to SQLite structural metadata used by the
frozen schema manifest: user_version, user tables, normalized CREATE SQL,
columns, foreign keys, and indexes.  Callers own the connection mode; this
module issues only metadata PRAGMA/SELECT statements.
"""

from __future__ import annotations

import re
import sqlite3
from typing import Any, Dict, Optional, Sequence


def normalise_sql(value: Optional[str]) -> Optional[str]:
    """Normalize SQLite DDL whitespace without changing its SQL tokens."""

    if value is None:
        return None
    return re.sub(r"\s+", " ", str(value).strip())


def quote_identifier(value: str) -> str:
    """Quote one SQLite identifier for metadata PRAGMA statements."""

    return '"' + str(value).replace('"', '""') + '"'


def connection_shape(connection: sqlite3.Connection) -> Dict[str, Any]:
    """Return the deterministic structural shape of a SQLite connection."""

    tables: Dict[str, Any] = {}
    rows = connection.execute(
        "SELECT name, sql FROM sqlite_master "
        "WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
    ).fetchall()
    for table_row in rows:
        name = str(table_row[0])
        quoted = quote_identifier(name)
        columns = []
        for row in connection.execute(f"PRAGMA table_info({quoted})").fetchall():
            columns.append(
                {
                    "name": str(row[1]),
                    "declared_type": str(row[2] or ""),
                    "not_null": bool(row[3]),
                    "default": row[4],
                    "primary_key": int(row[5]),
                }
            )
        foreign_keys = []
        for row in connection.execute(f"PRAGMA foreign_key_list({quoted})").fetchall():
            foreign_keys.append(
                {
                    "id": int(row[0]),
                    "seq": int(row[1]),
                    "table": str(row[2]),
                    "from": str(row[3]),
                    "to": str(row[4]),
                    "on_update": str(row[5]),
                    "on_delete": str(row[6]),
                    "match": str(row[7]),
                }
            )
        foreign_keys.sort(key=lambda item: (item["id"], item["seq"], item["from"]))
        indexes = []
        for row in connection.execute(f"PRAGMA index_list({quoted})").fetchall():
            index_name = str(row[1])
            index_quoted = quote_identifier(index_name)
            index_columns = [
                None if item[2] is None else str(item[2])
                for item in connection.execute(
                    f"PRAGMA index_info({index_quoted})"
                ).fetchall()
            ]
            indexes.append(
                {
                    "name": index_name,
                    "unique": bool(row[2]),
                    "origin": str(row[3]),
                    "partial": bool(row[4]),
                    "columns": index_columns,
                }
            )
        indexes.sort(key=lambda item: item["name"])
        tables[name] = {
            "sql": normalise_sql(table_row[1]),
            "columns": columns,
            "foreign_keys": foreign_keys,
            "indexes": indexes,
        }
    return {
        "user_version": int(connection.execute("PRAGMA user_version").fetchone()[0]),
        "tables": tables,
    }


def shape_from_ddl(ddl: str, transforms: Sequence[str] = ()) -> Dict[str, Any]:
    """Build a shape from isolated in-memory DDL and optional transformations."""

    connection = sqlite3.connect(":memory:")
    try:
        connection.executescript(ddl)
        for statement in transforms:
            connection.execute(statement)
        connection.commit()
        return connection_shape(connection)
    finally:
        connection.close()


__all__ = [
    "connection_shape",
    "normalise_sql",
    "quote_identifier",
    "shape_from_ddl",
]
