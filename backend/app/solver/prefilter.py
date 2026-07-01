"""Shrink the search space before solving (plan §6).

Three passes, cheap and big payoff:

1. **Level cap** — drop items above the build level.
2. **Relevance** — drop items that touch none of the dims the request cares
   about (and that aren't part of a set / don't carry a condition).
3. **Pareto dominance** — inside a slot, an item beaten on every relevant dim by
   another is useless. *Never* prune set items (they may unlock a bonus) nor
   conditional items (the condition cost isn't captured by stat dominance).
"""

from __future__ import annotations

from app import config
from app.data.repository import Item, SetDef
from app.solver.model import BuildParams, _condition_dims

# how many items of a slot a build may equip at once — dominance may only prune
# an item when at least this many *other* items dominate it.
SLOT_CAPACITY: dict[str, int] = {s: 1 for s in config.SLOTS_SIMPLES}
SLOT_CAPACITY["anneau"] = config.MAX_ANNEAUX
SLOT_CAPACITY["dofus"] = config.MAX_DOFUS_TROPHEE
SLOT_CAPACITY["trophee"] = config.MAX_DOFUS_TROPHEE


def objective_value_dims(params: BuildParams) -> set[str]:
    dims: set[str] = set()
    if params.objective.mode == "wisdom":
        dims.add("sagesse")
        dims.update(params.tiebreak_weights.keys())
    for carac, do_elem in params.objective.elements:
        dims.update({carac, do_elem, "puissance", "pct_do", "do_fixe"})
    dims.update(params.objective.profile_dims)
    return dims


def _maximize_and_guard(params: BuildParams) -> tuple[set[str], set[str]]:
    maximize = objective_value_dims(params)
    guard: set[str] = set()
    for c in params.constraints:
        if c["op"] in (">=", ">"):
            maximize.add(c["dim"])
        else:  # <=, <, ==, != : direction not "more is better"
            guard.add(c["dim"])
    return maximize, guard


def prefilter(
    items: list[Item],
    sets: dict[int, SetDef],
    params: BuildParams,
) -> list[Item]:
    maximize, guard = _maximize_and_guard(params)
    relevant = maximize | guard

    # a set only matters if one of its tier bonuses touches a relevant dim;
    # items of an irrelevant set are treated as plain (and may be pruned).
    relevant_sets = {
        sid
        for sid, sd in sets.items()
        if any(d in relevant for tier in sd.bonuses.values() for d in tier)
    }

    # 1 + 2 : level cap and relevance
    kept: list[Item] = []
    for it in items:
        if it.level > params.level:
            continue
        in_set = it.set_id in relevant_sets
        has_cond = bool(it.conditions) and it.conditions.get("op") != "true"
        touches = any(it.stats.get(d) for d in relevant) or bool(
            _condition_dims(it.conditions) & relevant
        )
        if touches or in_set or has_cond:
            kept.append(it)

    # 3 : Pareto dominance per slot, among plain items only
    by_slot: dict[str, list[Item]] = {}
    protected: list[Item] = []
    for it in kept:
        in_set = it.set_id in relevant_sets
        has_cond = bool(it.conditions) and it.conditions.get("op") != "true"
        if in_set or has_cond:
            protected.append(it)
        else:
            by_slot.setdefault(it.slot, []).append(it)

    survivors: list[Item] = list(protected)
    for slot, slot_items in by_slot.items():
        capacity = SLOT_CAPACITY.get(slot, 1)
        survivors.extend(_pareto(slot_items, maximize, guard, capacity))
    return survivors


def _pareto(items: list[Item], maximize: set[str], guard: set[str], capacity: int) -> list[Item]:
    """Keep an item unless at least ``capacity`` kept items dominate it.

    For a single-select slot (capacity 1) this is ordinary Pareto pruning. For a
    multi-select slot (2 rings, 6 Dofus/Trophée) an item is only useless if
    enough strictly-better items exist to fill every slot it could occupy.
    """
    if len(items) <= capacity:
        return items
    maxd = sorted(maximize)
    guardd = sorted(guard)
    # heaviest first so dominators are seen before the items they dominate
    order = sorted(items, key=lambda it: -sum(it.stats.get(d, 0) for d in maxd))
    kept: list[Item] = []
    for cand in order:
        dominators = 0
        for keep in kept:
            if any(keep.stats.get(d, 0) != cand.stats.get(d, 0) for d in guardd):
                continue
            if all(keep.stats.get(d, 0) >= cand.stats.get(d, 0) for d in maxd):
                dominators += 1
                if dominators >= capacity:
                    break
        if dominators < capacity:
            kept.append(cand)
    return kept
