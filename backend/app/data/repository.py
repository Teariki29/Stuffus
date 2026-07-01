"""Load the SQLite item/set database into lightweight domain objects."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[2] / "data" / "items.sqlite"


@dataclass(slots=True)
class Item:
    id: int
    name: str
    slot: str
    type_name: str
    level: int
    set_id: int | None
    is_weapon: bool
    obtainable: bool
    stats: dict[str, int]
    conditions: dict | None
    weapon: dict | None
    img_url: str | None


@dataclass(slots=True)
class SetDef:
    id: int
    name: str
    item_ids: list[int]
    # tier (int) -> {dim: value}
    bonuses: dict[int, dict[str, int]] = field(default_factory=dict)

    @property
    def tiers(self) -> list[int]:
        return sorted(self.bonuses)


@dataclass(slots=True)
class Database:
    items: list[Item]
    sets: dict[int, SetDef]

    def items_by_slot(self) -> dict[str, list[Item]]:
        out: dict[str, list[Item]] = {}
        for it in self.items:
            out.setdefault(it.slot, []).append(it)
        return out


def _row_to_item(row: sqlite3.Row) -> Item:
    return Item(
        id=row["id"],
        name=row["name"],
        slot=row["slot"],
        type_name=row["type_name"],
        level=row["level"],
        set_id=row["set_id"],
        is_weapon=bool(row["is_weapon"]),
        obtainable=bool(row["obtainable"]),
        stats=json.loads(row["stats_json"]),
        conditions=json.loads(row["conditions_json"]) if row["conditions_json"] else None,
        weapon=json.loads(row["weapon_json"]) if row["weapon_json"] else None,
        img_url=row["img_url"],
    )


def load_database(db_path: Path | str = DB_PATH) -> Database:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        items = [_row_to_item(r) for r in conn.execute("SELECT * FROM items")]
        sets: dict[int, SetDef] = {}
        for r in conn.execute("SELECT * FROM sets"):
            bonuses_raw = json.loads(r["bonuses_json"])
            sets[r["id"]] = SetDef(
                id=r["id"],
                name=r["name"],
                item_ids=json.loads(r["item_ids"]),
                bonuses={int(k): v for k, v in bonuses_raw.items()},
            )
    finally:
        conn.close()
    return Database(items=items, sets=sets)


@lru_cache(maxsize=1)
def get_database() -> Database:
    """Cached singleton database (loaded once per process)."""
    return load_database()
