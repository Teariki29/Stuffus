"""Response models (plan §7)."""

from __future__ import annotations

from pydantic import BaseModel


class ResultItem(BaseModel):
    id: int
    name: str
    slot: str
    type_name: str | None = None
    level: int
    set_id: int | None = None
    img_url: str | None = None
    stats: dict[str, int] = {}
    conditions: dict | None = None
    conditions: dict | None = None


class ActiveSet(BaseModel):
    set_id: int
    name: str
    pieces: int
    bonus: dict[str, int] = {}


class Kpi(BaseModel):
    damage_normal: int | None = None
    damage_crit: int | None = None
    cc: int = 0
    resistances: dict[str, int] = {}


class BuildResponse(BaseModel):
    status: str
    optimality_gap: float
    items: list[ResultItem] = []
    point_allocation: dict[str, int] = {}
    totals: dict[str, int] = {}
    kpi: Kpi = Kpi()
    active_sets: list[ActiveSet] = []
    message: str | None = None
