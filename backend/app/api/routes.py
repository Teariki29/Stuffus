"""HTTP routes (plan §7)."""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.data.repository import get_database
from app.models.request import OptimizeRequest
from app.models.response import BuildResponse
from app.solver.service import optimize

router = APIRouter()


@router.post("/optimize", response_model=BuildResponse)
def post_optimize(req: OptimizeRequest) -> BuildResponse:
    return optimize(req)


@router.get("/items")
def get_items(
    slot: str | None = None,
    level_max: int | None = Query(default=None, ge=1, le=200),
    search: str | None = None,
    limit: int = Query(default=50, ge=1, le=500),
):
    db = get_database()
    out = []
    needle = search.lower() if search else None
    for it in db.items:
        if slot and it.slot != slot:
            continue
        if level_max is not None and it.level > level_max:
            continue
        if needle and needle not in it.name.lower():
            continue
        out.append(
            {
                "id": it.id,
                "name": it.name,
                "slot": it.slot,
                "level": it.level,
                "set_id": it.set_id,
                "img_url": it.img_url,
                "stats": it.stats,
            }
        )
        if len(out) >= limit:
            break
    return {"count": len(out), "items": out}


@router.get("/sets")
def get_sets():
    db = get_database()
    return {
        "count": len(db.sets),
        "sets": [
            {
                "id": s.id,
                "name": s.name,
                "item_ids": s.item_ids,
                "bonuses": s.bonuses,
            }
            for s in db.sets.values()
        ],
    }


@router.get("/health")
def health():
    db = get_database()
    return {"status": "ok", "items": len(db.items), "sets": len(db.sets)}
