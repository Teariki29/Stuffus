"""Glue between the HTTP request and the CP-SAT solver."""

from __future__ import annotations

from app.data.repository import get_database
from app.models.request import OptimizeRequest
from app.models.response import ActiveSet, BuildResponse, Kpi, ResultItem
from app.solver import stats as S
from app.solver.model import BuildParams, ObjectiveSpec
from app.solver.solve import solve

_INFEASIBLE_HELP = (
    "Aucun build ne satisfait toutes les contraintes. "
    "Essayez d'assouplir ou de retirer certaines contraintes."
)

# damage profile -> extra % dim folded into the damage coefficient
_PROFILE_DIMS: dict[str, list[str]] = {
    "generique": [],
    "melee": ["pct_do_melee"],
    "distance": ["pct_do_distance"],
    "sorts": ["pct_do_sorts"],
    "armes": ["pct_do_armes"],
}


def _objective(req: OptimizeRequest) -> ObjectiveSpec:
    if req.stuff_type == "sagesse":
        return ObjectiveSpec(mode="wisdom")
    profile = _PROFILE_DIMS.get(req.damage_profile, [])
    if req.stuff_type == "multi":
        elements = [(S.ELEMENT_MAP[e][0], S.ELEMENT_MAP[e][1]) for e in req.elements]
        return ObjectiveSpec(mode="damage", elements=elements, profile_dims=profile)
    carac, do_elem = S.STUFF_TYPE_MAP[req.stuff_type]
    return ObjectiveSpec(mode="damage", elements=[(carac, do_elem)], profile_dims=profile)


def _params(req: OptimizeRequest) -> BuildParams:
    constraints = [
        {"dim": c.dim, "op": ("==" if c.op == "=" else c.op), "value": c.value}
        for c in req.constraints
    ]
    return BuildParams(
        objective=_objective(req),
        level=req.level,
        constraints=constraints,
        allocate_points=req.allocate_points,
        obtainable_only=req.obtainable_only,
        banned_ids=list(req.banned_ids),
        tiebreak_weights=dict(req.tiebreak_weights),
    )


def optimize(req: OptimizeRequest) -> BuildResponse:
    db = get_database()
    params = _params(req)
    result = solve(db.items, db.sets, params, time_limit=req.time_limit)

    if result.status in ("INFEASIBLE", "UNKNOWN", "MODEL_INVALID"):
        return BuildResponse(
            status=result.status,
            optimality_gap=result.optimality_gap,
            message=_INFEASIBLE_HELP if result.status == "INFEASIBLE"
            else "Aucune solution trouvée dans le temps imparti.",
        )

    id2 = {it.id: it for it in db.items}
    items = [
        ResultItem(
            id=it.id,
            name=it.name,
            slot=it.slot,
            type_name=it.type_name,
            level=it.level,
            set_id=it.set_id,
            img_url=it.img_url,
            stats=it.stats,
            conditions=it.conditions,
        )
        for iid in result.item_ids
        if (it := id2.get(iid))
    ]
    active_sets = [
        ActiveSet(
            set_id=a["set_id"],
            name=db.sets[a["set_id"]].name if a["set_id"] in db.sets else str(a["set_id"]),
            pieces=a["pieces"],
            bonus=db.sets[a["set_id"]].bonuses.get(a["pieces"], {})
            if a["set_id"] in db.sets
            else {},
        )
        for a in result.active_sets
    ]
    return BuildResponse(
        status=result.status,
        optimality_gap=result.optimality_gap,
        items=items,
        point_allocation=result.point_allocation,
        totals=result.totals,
        kpi=Kpi(**result.kpi),
        active_sets=active_sets,
    )
