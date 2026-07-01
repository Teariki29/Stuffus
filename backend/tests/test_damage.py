"""P2 validation: the integer-scaled damage must equal the float KPI formula."""

from app.config import DAMAGE_SCALE
from app.solver.damage import damage_coeffs, multi_damage, theoretical_damage


def test_hand_computed_value():
    totals = {
        "force": 800,
        "puissance": 200,
        "pct_do": 50,
        "do_fixe": 30,
        "do_terre": 40,
    }
    # D = 100*(1 + (800+200+50)/100) + 30 + 40 = 100*11.5 + 70 = 1220
    assert theoretical_damage(totals, "force", "do_terre") == 1220


def test_scaled_matches_float():
    totals = {
        "force": 723,
        "puissance": 137,
        "pct_do": 22,
        "do_fixe": 41,
        "do_terre": 58,
        "intelligence": 999,  # irrelevant dim must not leak in
    }
    coeffs, const = damage_coeffs("force", "do_terre")
    scaled = const + sum(coeffs.get(d, 0) * v for d, v in totals.items())
    assert scaled / DAMAGE_SCALE == theoretical_damage(totals, "force", "do_terre")


def test_crit_adds_do_critiques():
    totals = {"force": 100, "do_critiques": 25}
    normal = theoretical_damage(totals, "force", "do_terre")
    crit = theoretical_damage(totals, "force", "do_terre", crit=True)
    assert crit - normal == 25


def test_multi_is_average():
    totals = {"force": 100, "intelligence": 300, "do_terre": 10, "do_feu": 0}
    d_terre = theoretical_damage(totals, "force", "do_terre")
    d_feu = theoretical_damage(totals, "intelligence", "do_feu")
    avg = multi_damage(totals, [("force", "do_terre"), ("intelligence", "do_feu")])
    assert avg == (d_terre + d_feu) / 2
