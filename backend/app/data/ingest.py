"""Ingestion: pull raw data once and cache it on disk.

Sources (see README / plan §1, §4.3):

* **dofusdude** (https://api.dofusdu.de) — clean *typed* effects with explicit
  min/max rolls, slot types and per-tier set bonuses. Primary source.
* **DofusDB** (https://api.dofusdb.fr) — the ``criterions`` strings (equip
  conditions) which dofusdude does not expose in bulk. Joined by ankama id.

Everything is written to ``backend/data/raw/`` as JSON. Re-run with ``--force``
to refresh the cache; otherwise existing files are reused (one crawl only,
respectful of both APIs).
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import httpx

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"

DOFUSDUDE = "https://api.dofusdu.de/dofus3/v1/fr"
DOFUSDB = "https://api.dofusdb.fr"

PAGE_SIZE = 1000
SETS_PAGE_SIZE = 500  # the /sets endpoint rejects page sizes above ~500
DOFUSDB_BATCH = 50  # DofusDB caps $limit at 50

EQUIP_FILE = RAW_DIR / "dofusdude_equipment.json"
SETS_FILE = RAW_DIR / "dofusdude_sets.json"
# per-item DofusDB enrichment: {id: {"crit": str, "set": int, "flags": int}}
DB_META_FILE = RAW_DIR / "dofusdb_item_meta.json"
# dofusdude structured equip conditions: {id: condition_tree}
CONDITIONS_FILE = RAW_DIR / "dofusdude_conditions.json"


def _get(client: httpx.Client, url: str, params=None, *, retries: int = 4) -> dict:
    last_exc: Exception | None = None
    for attempt in range(retries):
        try:
            r = client.get(url, params=params, timeout=60)
            r.raise_for_status()
            return r.json()
        except Exception as exc:  # noqa: BLE001 - want to retry on anything transient
            last_exc = exc
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"GET {url} failed after {retries} tries: {last_exc}")


def fetch_equipment(client: httpx.Client) -> list[dict]:
    """All equipment (incl. weapons) with typed effects."""
    items: list[dict] = []
    page = 1
    while True:
        data = _get(
            client,
            f"{DOFUSDUDE}/items/equipment",
            params={"page[size]": PAGE_SIZE, "page[number]": page, "fields[item]": "effects"},
        )
        batch = data.get("items", [])
        items.extend(batch)
        print(f"  equipment page {page}: +{len(batch)} (total {len(items)})")
        if not data.get("_links", {}).get("next") or not batch:
            break
        page += 1
    return items


def fetch_sets(client: httpx.Client) -> list[dict]:
    """All sets with per-tier effects and member item ids."""
    sets: list[dict] = []
    page = 1
    while True:
        data = _get(
            client,
            f"{DOFUSDUDE}/sets",
            params={
                "page[size]": SETS_PAGE_SIZE,
                "page[number]": page,
                "fields[set]": "effects",
            },
        )
        batch = data.get("sets", [])
        sets.extend(batch)
        print(f"  sets page {page}: +{len(batch)} (total {len(sets)})")
        if not data.get("_links", {}).get("next") or not batch:
            break
        page += 1
    return sets


def fetch_dofusdb_meta(client: httpx.Client, ids: list[int]) -> dict[str, dict]:
    """``{ankama_id: {"crit": str, "set": int}}`` from DofusDB, batched by id.

    Gives both the equip conditions (``criterions``) and the set membership
    (``itemSetId``); dofusdude exposes neither in bulk.
    """
    out: dict[str, dict] = {}
    n_batches = (len(ids) + DOFUSDB_BATCH - 1) // DOFUSDB_BATCH
    for bi, start in enumerate(range(0, len(ids), DOFUSDB_BATCH)):
        chunk = ids[start : start + DOFUSDB_BATCH]
        params: list[tuple[str, object]] = [
            ("$limit", DOFUSDB_BATCH),
            ("$select[]", "id"),
            ("$select[]", "criterions"),
            ("$select[]", "itemSetId"),
            ("$select[]", "m_flags"),
        ]
        params += [("id[$in][]", i) for i in chunk]
        data = _get(client, f"{DOFUSDB}/items", params=params)
        for row in data.get("data", []):
            crit = row.get("criterions") or ""
            set_id = row.get("itemSetId")
            if set_id is not None and int(set_id) < 0:
                set_id = None
            entry: dict = {"flags": int(row.get("m_flags") or 0)}
            if crit:
                entry["crit"] = crit
            if set_id is not None:
                entry["set"] = int(set_id)
            out[str(row["id"])] = entry
        if bi % 10 == 0:
            print(f"  dofusdb meta batch {bi + 1}/{n_batches} (found {len(out)})")
    return out


def fetch_conditions(client: httpx.Client, ids: list[int]) -> dict[str, dict]:
    """``{ankama_id: condition_tree}`` from dofusdude per-item detail.

    dofusdude resolves equip conditions into a *named* tree (element name +
    operator + value), which is far more reliable than decoding DofusDB's raw
    2-letter criterion codes. Only called for items that actually have a
    condition (per the DofusDB ``criterions`` field), so ~hundreds of calls.
    """
    out: dict[str, dict] = {}
    for n, iid in enumerate(ids):
        data = _get(client, f"{DOFUSDUDE}/items/equipment/{iid}")
        cond = data.get("conditions")
        if cond:
            out[str(iid)] = cond
        if n % 100 == 0:
            print(f"  conditions {n + 1}/{len(ids)} (found {len(out)})")
    return out


def run(force: bool = False) -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    with httpx.Client(headers={"User-Agent": "dofus-optimizer/0.1 (personal project)"}) as client:
        if force or not EQUIP_FILE.exists():
            print("Fetching equipment from dofusdude…")
            equipment = fetch_equipment(client)
            EQUIP_FILE.write_text(json.dumps(equipment, ensure_ascii=False), encoding="utf-8")
            print(f"  -> {EQUIP_FILE} ({len(equipment)} items)")
        else:
            equipment = json.loads(EQUIP_FILE.read_text(encoding="utf-8"))
            print(f"Using cached equipment ({len(equipment)} items)")

        if force or not SETS_FILE.exists():
            print("Fetching sets from dofusdude…")
            sets = fetch_sets(client)
            SETS_FILE.write_text(json.dumps(sets, ensure_ascii=False), encoding="utf-8")
            print(f"  -> {SETS_FILE} ({len(sets)} sets)")
        else:
            print("Using cached sets")

        if force or not DB_META_FILE.exists():
            print("Fetching item meta (criterions + set ids) from DofusDB…")
            ids = [it["ankama_id"] for it in equipment]
            meta = fetch_dofusdb_meta(client, ids)
            DB_META_FILE.write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")
            n_crit = sum(1 for v in meta.values() if "crit" in v)
            n_set = sum(1 for v in meta.values() if "set" in v)
            print(f"  -> {DB_META_FILE} ({n_crit} with conditions, {n_set} in a set)")
        else:
            meta = json.loads(DB_META_FILE.read_text(encoding="utf-8"))
            print("Using cached item meta")

        if force or not CONDITIONS_FILE.exists():
            print("Fetching structured conditions from dofusdude…")
            cond_ids = [int(i) for i, v in meta.items() if "crit" in v]
            conditions = fetch_conditions(client, cond_ids)
            CONDITIONS_FILE.write_text(json.dumps(conditions, ensure_ascii=False), encoding="utf-8")
            print(f"  -> {CONDITIONS_FILE} ({len(conditions)} conditions)")
        else:
            print("Using cached conditions")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Pull raw Dofus data into backend/data/raw/")
    ap.add_argument("--force", action="store_true", help="ignore cache and re-crawl")
    args = ap.parse_args()
    run(force=args.force)
    print("Done.", file=sys.stderr)
