"""Normalise raw dumps into ``backend/data/items.sqlite`` (plan §4.2 / §4.3).

Run after :mod:`app.data.ingest`::

    python -m app.data.normalize
"""

from __future__ import annotations

import json
import sqlite3
import sys
import time
from collections import defaultdict
from pathlib import Path

from app.config import (
    EXCLUDED_NAME_SUBSTRINGS,
    EXCLUDED_TYPE_SUBSTRINGS,
    OBTAINABLE_ALLOWLIST,
    OBTAINABLE_FLAG_BIT,
    OBTAINABLE_KEEP_SLOTS,
    TYPE_TO_SLOT,
    WEAPON_TYPE_NAMES,
)
from app.data.criterion_parser import parse_criterion, parse_dofusdude_condition
from app.data.effect_mapping import (
    EFFECT_TO_DIM,
    WEAPON_HIT_ELEMENT,
    WEAPON_HIT_NAMES,
    roll_value,
)

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
RAW_DIR = DATA_DIR / "raw"
DB_PATH = DATA_DIR / "items.sqlite"
SCHEMA = Path(__file__).resolve().parent / "schema.sql"

EQUIP_FILE = RAW_DIR / "dofusdude_equipment.json"
SETS_FILE = RAW_DIR / "dofusdude_sets.json"
DB_META_FILE = RAW_DIR / "dofusdb_item_meta.json"
CONDITIONS_FILE = RAW_DIR / "dofusdude_conditions.json"


def _excluded(type_name: str) -> bool:
    return any(s in type_name for s in EXCLUDED_TYPE_SUBSTRINGS)


def normalize_item(raw: dict, meta: dict, conditions: dict) -> dict | None:
    """Return a row dict for ``items`` or ``None`` if the item is irrelevant."""
    type_name = raw.get("type", {}).get("name", "")
    if _excluded(type_name):
        return None
    name = raw.get("name", "")
    if any(s in name for s in EXCLUDED_NAME_SUBSTRINGS):
        return None
    slot = TYPE_TO_SLOT.get(type_name)
    if slot is None:
        return None

    iid = raw["ankama_id"]
    is_weapon = type_name in WEAPON_TYPE_NAMES
    stats: dict[str, int] = defaultdict(int)
    weapon_hits: list[dict] = []

    for eff in raw.get("effects", []):
        name = eff.get("type", {}).get("name")
        if name is None:
            continue
        if name in WEAPON_HIT_NAMES:
            weapon_hits.append(
                {
                    "element": WEAPON_HIT_ELEMENT.get(name, "neutre"),
                    "min": int(eff.get("int_minimum", 0)),
                    "max": int(eff.get("int_maximum", 0)) or int(eff.get("int_minimum", 0)),
                    "steal": name.startswith("vol"),
                }
            )
            continue
        dim = EFFECT_TO_DIM.get(name)
        if dim is None:
            continue
        val = roll_value(eff)
        if val:
            stats[dim] += val

    item_meta = meta.get(str(iid), {})
    set_id = item_meta.get("set")
    # prefer dofusdude's resolved condition tree (mapped by element name);
    # fall back to parsing the raw DofusDB criterion string if absent.
    dd_cond = conditions.get(str(iid))
    crit_tree = parse_dofusdude_condition(dd_cond) if dd_cond else parse_criterion(item_meta.get("crit"))
    flags = item_meta.get("flags", 0)
    obtainable = (
        bool(flags & OBTAINABLE_FLAG_BIT)
        or slot in OBTAINABLE_KEEP_SLOTS
        or iid in OBTAINABLE_ALLOWLIST
    )

    weapon_json = None
    if is_weapon:
        weapon_json = json.dumps({"hits": weapon_hits}, ensure_ascii=False)

    return {
        "id": iid,
        "name": raw.get("name", ""),
        "slot": slot,
        "type_name": type_name,
        "level": int(raw.get("level", 0)),
        "set_id": set_id,
        "is_weapon": int(is_weapon),
        "obtainable": int(obtainable),
        "stats_json": json.dumps(dict(stats), ensure_ascii=False),
        "conditions_json": json.dumps(crit_tree, ensure_ascii=False) if crit_tree else None,
        "weapon_json": weapon_json,
        "img_url": (raw.get("image_urls") or {}).get("icon"),
    }


def normalize_set(raw: dict, members: list[int]) -> dict:
    bonuses: dict[str, dict[str, int]] = {}
    for tier, effects in (raw.get("effects") or {}).items():
        if not effects:
            continue
        tier_vec: dict[str, int] = defaultdict(int)
        for eff in effects:
            name = eff.get("type", {}).get("name")
            dim = EFFECT_TO_DIM.get(name)
            if dim is None:
                continue
            val = roll_value(eff)
            if val:
                tier_vec[dim] += val
        if tier_vec:
            bonuses[str(tier)] = dict(tier_vec)
    return {
        "id": raw["ankama_id"],
        "name": raw.get("name", ""),
        "item_ids": json.dumps(sorted(members)),
        "bonuses_json": json.dumps(bonuses, ensure_ascii=False),
    }


def run() -> None:
    equipment = json.loads(EQUIP_FILE.read_text(encoding="utf-8"))
    sets_raw = json.loads(SETS_FILE.read_text(encoding="utf-8"))
    meta = json.loads(DB_META_FILE.read_text(encoding="utf-8"))
    conditions = (
        json.loads(CONDITIONS_FILE.read_text(encoding="utf-8"))
        if CONDITIONS_FILE.exists()
        else {}
    )

    # build items
    rows: list[dict] = []
    members_by_set: dict[int, list[int]] = defaultdict(list)
    dropped = 0
    for raw in equipment:
        row = normalize_item(raw, meta, conditions)
        if row is None:
            dropped += 1
            continue
        rows.append(row)
        if row["set_id"] is not None:
            members_by_set[row["set_id"]].append(row["id"])

    # build sets (only those that actually have member items kept)
    set_rows = [
        normalize_set(s, members_by_set.get(s["ankama_id"], []))
        for s in sets_raw
        if members_by_set.get(s["ankama_id"])
    ]

    DB_PATH.unlink(missing_ok=True)
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.executescript(SCHEMA.read_text(encoding="utf-8"))
        conn.executemany(
            """INSERT INTO items
               (id,name,slot,type_name,level,set_id,is_weapon,obtainable,
                stats_json,conditions_json,weapon_json,img_url)
               VALUES
               (:id,:name,:slot,:type_name,:level,:set_id,:is_weapon,:obtainable,
                :stats_json,:conditions_json,:weapon_json,:img_url)""",
            rows,
        )
        conn.executemany(
            """INSERT INTO sets (id,name,item_ids,bonuses_json)
               VALUES (:id,:name,:item_ids,:bonuses_json)""",
            set_rows,
        )
        conn.executemany(
            "INSERT INTO meta (key,value) VALUES (?,?)",
            [
                ("ingested_at", time.strftime("%Y-%m-%dT%H:%M:%S")),
                ("source_effects", "dofusdude api.dofusdu.de (dofus3/fr)"),
                ("source_conditions", "dofusdb api.dofusdb.fr (criterions, itemSetId)"),
                ("n_items", str(len(rows))),
                ("n_sets", str(len(set_rows))),
            ],
        )
        conn.commit()
    finally:
        conn.close()

    print(f"Items kept: {len(rows)} (dropped {dropped} irrelevant)")
    print(f"Sets kept:  {len(set_rows)}")
    print(f"-> {DB_PATH}")


if __name__ == "__main__":
    run()
    print("Done.", file=sys.stderr)
