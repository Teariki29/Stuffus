"""Build the CP-SAT model (plan §5).

One model holds the whole problem: item selection (binary), characteristic point
allocation (integer tranches), set-bonus tiers (linearised binaries), equip
conditions (indicators) and a linear damage objective. ``solve.py`` drives it,
including the special objectives (multi-element average, wisdom lexicographic).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ortools.sat.python import cp_model

from app import config
from app.data.repository import Item, SetDef
from app.solver import stats as S

# operator -> normalised integer comparison
_NEG = {">=": "<", "<=": ">", ">": "<=", "<": ">=", "==": "!=", "!=": "=="}


def _norm_op(op: str) -> str:
    return {">": ">", "<": "<", "=": "==", "!": "!=", ">=": ">=", "<=": "<=", "==": "==", "!=": "!="}[op]


@dataclass
class ObjectiveSpec:
    """What 'best' means for this request."""

    mode: str  # "damage" | "wisdom"
    # damage: list of (carac dim, do_elem dim) — 1 entry mono, N entries multi
    elements: list[tuple[str, str]] = field(default_factory=list)
    # extra % dims folded into the damage coefficient (melee/distance/sorts/armes)
    profile_dims: list[str] = field(default_factory=list)


@dataclass
class BuildParams:
    objective: ObjectiveSpec
    level: int
    constraints: list[dict] = field(default_factory=list)  # {dim, op, value}
    allocate_points: bool = True
    obtainable_only: bool = True
    tiebreak_weights: dict[str, int] = field(default_factory=dict)


class BuildModel:
    def __init__(self, items: list[Item], sets: dict[int, SetDef], params: BuildParams):
        self.items = items
        self.sets = sets
        self.params = params
        self.model = cp_model.CpModel()
        self.item_by_id = {it.id: it for it in items}

        self.x: dict[int, cp_model.IntVar] = {}
        self.invested: dict[str, cp_model.IntVar] = {}
        self.alloc: dict[str, list[cp_model.IntVar]] = {}
        self.z: dict[int, dict[int, cp_model.IntVar]] = {}
        self._total_cache: dict[str, cp_model.LinearExpr] = {}
        # count of active set bonuses (built in _build_sets when a condition
        # such as "< 3 bonus de panoplies" needs it); 0 means no set is active.
        self._nb_panoplies_expr: cp_model.LinearExpr | int = 0

        self._build_vars()
        self._build_slot_constraints()
        self._build_sets()
        self._build_point_allocation()
        self._build_conditions()
        self._build_user_constraints()

    # ------------------------------------------------------------------ vars
    def _needed_dims(self) -> set[str]:
        dims: set[str] = set()
        for carac, do_elem in self.params.objective.elements:
            dims.update({carac, do_elem, "puissance", "pct_do", "do_fixe"})
        dims.update(self.params.objective.profile_dims)
        if self.params.objective.mode == "wisdom":
            dims.add("sagesse")
            dims.update(self.params.tiebreak_weights.keys())
        for c in self.params.constraints:
            dims.add(c["dim"])
        for it in self.items:
            for d in _condition_dims(it.conditions):
                dims.add(d)
        return dims

    def _build_vars(self) -> None:
        for it in self.items:
            self.x[it.id] = self.model.NewBoolVar(f"x_{it.id}")

    def _build_slot_constraints(self) -> None:
        by_slot: dict[str, list[int]] = {}
        for it in self.items:
            by_slot.setdefault(it.slot, []).append(it.id)
        for slot in config.SLOTS_SIMPLES:
            ids = by_slot.get(slot, [])
            if ids:
                self.model.Add(sum(self.x[i] for i in ids) <= 1)
        if by_slot.get("anneau"):
            self.model.Add(sum(self.x[i] for i in by_slot["anneau"]) <= config.MAX_ANNEAUX)
        pool = by_slot.get("dofus", []) + by_slot.get("trophee", [])
        if pool:
            self.model.Add(sum(self.x[i] for i in pool) <= config.MAX_DOFUS_TROPHEE)

    # ------------------------------------------------------------------ sets
    def _build_sets(self) -> None:
        needed = self._needed_dims()
        # if any item requires a "< N bonus de panoplies" condition we must count
        # EVERY active set (even ones whose stats are irrelevant to the objective).
        count_panoplies = "nb_panoplies" in needed

        present: dict[int, list[int]] = {}
        for it in self.items:
            if it.set_id is not None and it.set_id in self.sets:
                present.setdefault(it.set_id, []).append(it.id)

        active_terms: list = []
        for set_id, member_ids in present.items():
            n_members = len(member_ids)
            if n_members < 2:
                continue  # a single owned piece can never trigger a set bonus
            sd = self.sets[set_id]
            relevant = any(d in needed for tier in sd.bonuses.values() for d in tier)
            n_s = sum(self.x[i] for i in member_ids)

            if relevant:
                zk = {k: self.model.NewBoolVar(f"z_{set_id}_{k}") for k in range(n_members + 1)}
                self.z[set_id] = zk
                self.model.Add(sum(zk.values()) == 1)
                self.model.Add(n_s == sum(k * zk[k] for k in zk))
                if count_panoplies:
                    # bonus active <=> at least 2 pieces <=> a tier k>=2 is chosen
                    active_terms.append(sum(zk[k] for k in zk if k >= 2))
            elif count_panoplies:
                # lightweight activation bool for a set whose stats we don't model
                active = self.model.NewBoolVar(f"act_{set_id}")
                self.model.Add(n_s >= 2).OnlyEnforceIf(active)
                self.model.Add(n_s <= 1).OnlyEnforceIf(active.Not())
                active_terms.append(active)

        if active_terms:
            self._nb_panoplies_expr = cp_model.LinearExpr.Sum(active_terms)

    def _set_bonus(self, set_id: int, k: int, dim: str) -> int:
        return self.sets[set_id].bonuses.get(k, {}).get(dim, 0)

    # --------------------------------------------------------- point alloc
    def _build_point_allocation(self) -> None:
        if not self.params.allocate_points:
            return
        budget = config.points_for_level(self.params.level)
        needed = self._needed_dims() & set(S.ALLOCATABLE_CARACS)
        cost_terms = []
        for carac in S.ALLOCATABLE_CARACS:
            if carac not in needed:
                continue
            tranches = config.TRANCHES_BY_CARAC[carac]
            vars_t = []
            for ti, (width, cost) in enumerate(tranches):
                a = self.model.NewIntVar(0, width, f"a_{carac}_{ti}")
                vars_t.append(a)
                cost_terms.append(cost * a)
            self.alloc[carac] = vars_t
            inv = self.model.NewIntVar(0, 10_000, f"inv_{carac}")
            self.model.Add(inv == sum(vars_t))
            self.invested[carac] = inv
        if cost_terms:
            self.model.Add(sum(cost_terms) <= budget)

    # ---------------------------------------------------------------- totals
    def total(self, dim: str) -> cp_model.LinearExpr:
        if dim == "nb_panoplies":  # pseudo-dim resolved to the active-set count
            return self._nb_panoplies_expr
        if dim in self._total_cache:
            return self._total_cache[dim]
        terms: list = []
        base = self._base_value(dim)
        for it in self.items:
            v = it.stats.get(dim)
            if v:
                terms.append(v * self.x[it.id])
        for set_id, zk in self.z.items():
            for k, zvar in zk.items():
                b = self._set_bonus(set_id, k, dim)
                if b:
                    terms.append(b * zvar)
        if dim in self.invested:
            terms.append(self.invested[dim])
        expr = cp_model.LinearExpr.Sum(terms) + base if terms else cp_model.LinearExpr.Sum([]) + base
        self._total_cache[dim] = expr
        return expr

    @staticmethod
    def _base_value(dim: str) -> int:
        return {
            "vitalite": config.BASE_LIFE,
            "pa": config.BASE_PA,
            "pm": config.BASE_PM,
            "po": config.BASE_PO,
            "cc": config.BASE_CC,
        }.get(dim, 0)

    # ------------------------------------------------------------ conditions
    def _add_cmp(self, expr, op: str, value: int, enforce=None) -> None:
        op = _norm_op(op)
        if op == ">":
            ct = self.model.Add(expr >= value + 1)
        elif op == "<":
            ct = self.model.Add(expr <= value - 1)
        elif op == ">=":
            ct = self.model.Add(expr >= value)
        elif op == "<=":
            ct = self.model.Add(expr <= value)
        elif op == "==":
            ct = self.model.Add(expr == value)
        else:  # "!="
            ct = self.model.Add(expr != value)
        if enforce is not None:
            ct.OnlyEnforceIf(enforce)

    def _reify(self, node: dict) -> cp_model.IntVar:
        """Return a BoolVar equivalent to the truth of a condition node."""
        op = node.get("op")
        if op == "true":
            b = self.model.NewBoolVar("cond_true")
            self.model.Add(b == 1)
            return b
        if op == "cmp":
            b = self.model.NewBoolVar("cond_cmp")
            expr = self.total(node["dim"])
            self._add_cmp(expr, node["operator"], node["value"], enforce=b)
            self._add_cmp(expr, _NEG[_norm_op(node["operator"])], node["value"], enforce=b.Not())
            return b
        # and / or
        children = [self._reify(c) for c in node["children"]]
        b = self.model.NewBoolVar(f"cond_{op}")
        if op == "and":
            for c in children:
                self.model.AddImplication(b, c)
            self.model.Add(sum(children) >= len(children)).OnlyEnforceIf(b)
            self.model.Add(sum(children) <= len(children) - 1).OnlyEnforceIf(b.Not())
        else:  # or
            self.model.Add(sum(children) >= 1).OnlyEnforceIf(b)
            self.model.Add(sum(children) == 0).OnlyEnforceIf(b.Not())
        return b

    def _build_conditions(self) -> None:
        for it in self.items:
            node = it.conditions
            if not node or node.get("op") == "true":
                continue
            self._enforce(node, self.x[it.id])

    def _enforce(self, node: dict, lit) -> None:
        """Enforce a condition node whenever ``lit`` (item is equipped)."""
        op = node.get("op")
        if op == "true":
            return
        if op == "cmp":
            self._add_cmp(self.total(node["dim"]), node["operator"], node["value"], enforce=lit)
        elif op == "and":
            for child in node["children"]:
                self._enforce(child, lit)
        elif op == "or":
            child_lits = [self._reify(c) for c in node["children"]]
            self.model.Add(sum(child_lits) >= 1).OnlyEnforceIf(lit)

    # ------------------------------------------------------ user constraints
    def _build_user_constraints(self) -> None:
        for c in self.params.constraints:
            self._add_cmp(self.total(c["dim"]), c["op"], int(c["value"]))


def _condition_dims(node: dict | None) -> set[str]:
    if not node:
        return set()
    op = node.get("op")
    if op == "cmp":
        return {node["dim"]}
    if op in ("and", "or"):
        out: set[str] = set()
        for c in node["children"]:
            out |= _condition_dims(c)
        return out
    return set()
