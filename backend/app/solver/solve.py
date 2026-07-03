"""Orchestrate model build + solve, including the special objectives (§5.8)."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from ortools.sat.python import cp_model

from app.solver import stats as S
from app.solver.damage import damage_coeffs, multi_damage
from app.solver.model import BuildModel, BuildParams
from app.solver.prefilter import prefilter

_STATUS = {
    cp_model.OPTIMAL: "OPTIMAL",
    cp_model.FEASIBLE: "FEASIBLE",
    cp_model.INFEASIBLE: "INFEASIBLE",
    cp_model.MODEL_INVALID: "MODEL_INVALID",
    cp_model.UNKNOWN: "UNKNOWN",
}


@dataclass
class SolveResult:
    status: str
    optimality_gap: float
    item_ids: list[int] = field(default_factory=list)
    point_allocation: dict[str, int] = field(default_factory=dict)
    totals: dict[str, int] = field(default_factory=dict)
    active_sets: list[dict] = field(default_factory=list)
    kpi: dict = field(default_factory=dict)
    objective_value: float = 0.0


def _damage_objective(bm: BuildModel):
    # the per-element constant offset does not affect the argmax, so we omit it
    # from the model objective (it is only used for KPI display).
    agg: dict[str, int] = defaultdict(int)
    profile = tuple(bm.params.objective.profile_dims)
    for carac, do_elem in bm.params.objective.elements:
        coeffs, _ = damage_coeffs(carac, do_elem, profile)
        for d, v in coeffs.items():
            agg[d] += v
    return cp_model.LinearExpr.Sum([v * bm.total(d) for d, v in agg.items()])


def _make_solver(time_limit: float) -> cp_model.CpSolver:
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit
    solver.parameters.num_search_workers = 8
    # The model is heavy on indicator (OnlyEnforceIf) constraints; the default
    # aggressive probing explodes into >100k binary clauses and eats the whole
    # time budget before search starts. Disabling it finds & proves the optimum
    # several times faster here.
    solver.parameters.cp_model_probing_level = 0
    return solver


def solve(
    items,
    sets,
    params: BuildParams,
    *,
    time_limit: float = 10.0,
    use_prefilter: bool = True,
) -> SolveResult:
    if params.banned_ids:
        banned = set(params.banned_ids)
        items = [it for it in items if it.id not in banned]
    if params.obtainable_only:
        items = [it for it in items if it.obtainable]
    if use_prefilter:
        items = prefilter(items, sets, params)
    bm = BuildModel(items, sets, params)
    model = bm.model

    if params.objective.mode == "wisdom":
        return _solve_wisdom(bm, time_limit)

    model.Maximize(_damage_objective(bm))
    solver = _make_solver(time_limit)
    status = solver.Solve(model)
    return _extract(bm, solver, status)


def _solve_wisdom(bm: BuildModel, time_limit: float) -> SolveResult:
    model = bm.model
    sagesse = bm.total("sagesse")

    # pass 1 — maximise total wisdom
    model.Maximize(sagesse)
    solver = _make_solver(time_limit / 2)
    status = solver.Solve(model)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return _extract(bm, solver, status)
    best_sagesse = round(solver.ObjectiveValue())

    # pass 2 — lock wisdom, maximise the weighted tiebreak
    model.Add(sagesse >= best_sagesse)
    weights = bm.params.tiebreak_weights or {"vitalite": 1}
    model.Maximize(cp_model.LinearExpr.Sum([w * bm.total(d) for d, w in weights.items()]))
    solver = _make_solver(time_limit / 2)
    status = solver.Solve(model)
    return _extract(bm, solver, status)


def _extract(bm: BuildModel, solver: cp_model.CpSolver, status) -> SolveResult:
    status_name = _STATUS.get(status, str(status))
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return SolveResult(status=status_name, optimality_gap=1.0)

    item_ids = [iid for iid, var in bm.x.items() if solver.Value(var) == 1]
    point_allocation = {c: solver.Value(v) for c, v in bm.invested.items() if solver.Value(v) > 0}

    totals: dict[str, int] = {}
    for dim in S.STATS:
        val = int(solver.Value(bm.total(dim)))
        if val:
            totals[dim] = val

    active_sets = []
    for set_id, zk in bm.z.items():
        for k, zvar in zk.items():
            if k >= 2 and solver.Value(zvar) == 1:
                active_sets.append({"set_id": set_id, "pieces": k})

    kpi = _compute_kpi(bm, totals)

    obj = solver.ObjectiveValue()
    bound = solver.BestObjectiveBound()
    gap = 0.0 if obj == 0 else abs(bound - obj) / max(abs(obj), 1e-9)

    return SolveResult(
        status=status_name,
        optimality_gap=round(gap, 4),
        item_ids=item_ids,
        point_allocation=point_allocation,
        totals=totals,
        active_sets=active_sets,
        kpi=kpi,
        objective_value=obj,
    )


def _compute_kpi(bm: BuildModel, totals: dict[str, int]) -> dict:
    kpi: dict = {
        "cc": totals.get("cc", 0),
        "resistances": {
            e: totals.get(f"res_{e}", 0)
            for e in ("terre", "feu", "eau", "air", "neutre")
        },
    }
    elements = bm.params.objective.elements
    if elements:
        profile = tuple(bm.params.objective.profile_dims)
        kpi["damage_normal"] = round(multi_damage(totals, elements, profile))
        kpi["damage_crit"] = round(multi_damage(totals, elements, profile, crit=True))
    return kpi
