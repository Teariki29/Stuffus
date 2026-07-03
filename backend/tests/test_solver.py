"""Solver tests: conditions (P6), multi & wisdom (P8), full build integration."""

import pytest

from app.data.repository import Item, get_database
from app.solver.model import BuildParams, ObjectiveSpec
from app.solver.solve import solve


def _amulette(iid, name, stats, conditions=None, obtainable=True):
    return Item(
        id=iid, name=name, slot="amulette", type_name="Amulette", level=1,
        set_id=None, is_weapon=False, obtainable=obtainable, stats=stats, conditions=conditions,
        weapon=None, img_url=None,
    )


# --------------------------------------------------------------- P6 conditions
def test_unsatisfiable_condition_excludes_item():
    a = _amulette(1, "BigIntButLocked", {"intelligence": 1000},
                  conditions={"op": "cmp", "dim": "force", "operator": ">=", "value": 999999})
    b = _amulette(2, "SmallIntFree", {"intelligence": 10})
    params = BuildParams(
        objective=ObjectiveSpec("damage", [("intelligence", "do_feu")]),
        level=1, allocate_points=False,
    )
    res = solve([a, b], {}, params, time_limit=5)
    assert res.status == "OPTIMAL"
    assert res.item_ids == [2]  # locked item cannot be worn


def test_satisfiable_condition_allows_item():
    a = _amulette(1, "BigIntOk", {"intelligence": 1000},
                  conditions={"op": "cmp", "dim": "force", "operator": ">=", "value": 0})
    b = _amulette(2, "SmallIntFree", {"intelligence": 10})
    params = BuildParams(
        objective=ObjectiveSpec("damage", [("intelligence", "do_feu")]),
        level=1, allocate_points=False,
    )
    res = solve([a, b], {}, params, time_limit=5)
    assert res.item_ids == [1]


def test_obtainable_only_filter():
    junk = _amulette(1, "NonObtainable", {"intelligence": 1000}, obtainable=False)
    legit = _amulette(2, "Obtainable", {"intelligence": 10}, obtainable=True)
    obj = ObjectiveSpec("damage", [("intelligence", "do_feu")])
    # default: the huge non-obtainable item is filtered out
    on = solve([junk, legit], {}, BuildParams(objective=obj, level=1, allocate_points=False))
    assert on.item_ids == [2]
    # toggled off: the solver may use it
    off = solve(
        [junk, legit],
        {},
        BuildParams(objective=obj, level=1, allocate_points=False, obtainable_only=False),
    )
    assert off.item_ids == [1]


def test_panoplie_count_condition():
    """A trophy requiring '< 1 bonus de panoplie' must not coexist with an active set."""
    # a 2-piece set (amulette + cape), bonus +100 force at 2 pieces
    from app.data.repository import SetDef

    a = Item(1, "SetAmu", "amulette", "Amulette", 1, 7, False, True, {"force": 50}, None, None, None)
    b = Item(2, "SetCape", "cape", "Cape", 1, 7, False, True, {"force": 50}, None, None, None)
    sets = {7: SetDef(7, "TestSet", [1, 2], {2: {"force": 100}})}
    # a strong trophy that forbids any active set bonus
    trophy = Item(
        3, "LoneTrophy", "trophee", "Trophée", 1, None, False, True,
        {"force": 1000}, {"op": "cmp", "dim": "nb_panoplies", "operator": "<", "value": 1},
        None, None,
    )
    obj = ObjectiveSpec("damage", [("force", "do_terre")])
    res = solve([a, b, trophy], sets, BuildParams(objective=obj, level=200, allocate_points=False))
    assert res.status == "OPTIMAL"
    assert 3 in res.item_ids  # the strong trophy is worth taking
    assert res.active_sets == []  # ...but only if no set bonus is active


def test_panoplie_count_tiers():
    """A k-piece set counts (k-1) bonuses: a trophy needing '< 2' caps the set at 2 pieces."""
    from app.data.repository import SetDef

    a = Item(1, "S1", "amulette", "Amulette", 1, 9, False, True, {"force": 30}, None, None, None)
    b = Item(2, "S2", "cape", "Cape", 1, 9, False, True, {"force": 30}, None, None, None)
    c = Item(3, "S3", "ceinture", "Ceinture", 1, 9, False, True, {"force": 30}, None, None, None)
    sets = {9: SetDef(9, "ThreeSet", [1, 2, 3], {2: {"force": 0}, 3: {"force": 0}})}
    trophy = Item(
        4, "BigTrophy", "trophee", "Trophée", 1, None, False, True,
        {"force": 1000}, {"op": "cmp", "dim": "nb_panoplies", "operator": "<", "value": 2},
        None, None,
    )
    obj = ObjectiveSpec("damage", [("force", "do_terre")])
    res = solve([a, b, c, trophy], sets, BuildParams(objective=obj, level=200, allocate_points=False))
    assert res.status == "OPTIMAL"
    assert 4 in res.item_ids  # the strong trophy is taken
    # count must stay < 2, i.e. the 3-piece set is capped at 2 pieces (count 1)
    set_pieces = sum(1 for i in (1, 2, 3) if i in res.item_ids)
    assert set_pieces == 2


def test_or_condition():
    # needs force>=999999 OR intelligence>=0  -> the OR is satisfiable
    a = _amulette(1, "OrLocked", {"intelligence": 1000},
                  conditions={"op": "or", "children": [
                      {"op": "cmp", "dim": "force", "operator": ">=", "value": 999999},
                      {"op": "cmp", "dim": "intelligence", "operator": ">=", "value": 0},
                  ]})
    params = BuildParams(
        objective=ObjectiveSpec("damage", [("intelligence", "do_feu")]),
        level=1, allocate_points=False,
    )
    res = solve([a], {}, params, time_limit=5)
    assert res.item_ids == [1]


# ----------------------------------------------------------- P8 multi / wisdom
@pytest.fixture(scope="module")
def db():
    return get_database()


def test_multi_element_runs(db):
    params = BuildParams(
        objective=ObjectiveSpec("damage", [("force", "do_terre"), ("agilite", "do_air")]),
        level=200,
        constraints=[{"dim": "pa", "op": ">=", "value": 11}],
    )
    res = solve(db.items, db.sets, params, time_limit=30)
    assert res.status in ("OPTIMAL", "FEASIBLE")
    assert res.totals.get("pa", 0) >= 11
    assert res.kpi["damage_normal"] > 0


def test_wisdom_maximises_sagesse(db):
    params = BuildParams(
        objective=ObjectiveSpec("wisdom"),
        level=200,
        tiebreak_weights={"vitalite": 1},
    )
    res = solve(db.items, db.sets, params, time_limit=30)
    assert res.status in ("OPTIMAL", "FEASIBLE")
    # a full level-200 wisdom build should clear a few hundred wisdom
    assert res.totals.get("sagesse", 0) > 200


# ------------------------------------------------------------ full build (P4)
def _cond_holds(node, totals):
    if not node or node.get("op") == "true":
        return True
    if node["op"] == "cmp":
        t, op, v = totals.get(node["dim"], 0), node["operator"], node["value"]
        return {
            ">": t > v, "<": t < v, ">=": t >= v, "<=": t <= v,
            "=": t == v, "==": t == v, "!": t != v, "!=": t != v,
        }[op]
    res = [_cond_holds(c, totals) for c in node["children"]]
    return all(res) if node["op"] == "and" else any(res)


@pytest.mark.parametrize("elem", [("force", "do_terre"), ("intelligence", "do_feu")])
def test_no_chosen_item_violates_its_condition(db, elem):
    params = BuildParams(
        objective=ObjectiveSpec("damage", [elem]),
        level=200,
        constraints=[{"dim": "pa", "op": ">=", "value": 11}],
    )
    res = solve(db.items, db.sets, params, time_limit=30)
    id2 = {it.id: it for it in db.items}
    for iid in res.item_ids:
        it = id2[iid]
        assert _cond_holds(it.conditions, res.totals), f"{it.name} violates {it.conditions}"


def test_full_build_respects_slot_caps(db):
    params = BuildParams(
        objective=ObjectiveSpec("damage", [("force", "do_terre")]),
        level=200,
        constraints=[{"dim": "pa", "op": ">=", "value": 11}, {"dim": "pm", "op": ">=", "value": 6}],
    )
    res = solve(db.items, db.sets, params, time_limit=30)
    assert res.status in ("OPTIMAL", "FEASIBLE")
    id2 = {it.id: it for it in db.items}
    slots = [id2[i].slot for i in res.item_ids]
    assert slots.count("anneau") <= 2
    assert slots.count("dofus") + slots.count("trophee") <= 6
    for simple in ("coiffe", "cape", "amulette", "ceinture", "bottes", "bouclier", "arme", "familier"):
        assert slots.count(simple) <= 1
    assert res.totals["pa"] >= 11 and res.totals["pm"] >= 6
