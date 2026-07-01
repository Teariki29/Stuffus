"""Theoretical-damage model (plan §5.8).

With *jet parfait* + *coup max* the damage of a hit is **linear** in the build's
stat vector::

    D = BASE * (1 + (carac + puissance + pct_do) / 100) + do_fixe + do_elem

We use a generic spell base (``BASE_GENERIQUE``) and the generic ``% Dommages``
only — per the frozen decision we do NOT add a spell-specific
``% Sort`` / ``% Mêlée`` / ``% Distance``. The base value never changes which
build is optimal; it only scales the displayed KPI.

Two faces of the same formula:

* :func:`theoretical_damage` — float, for KPI display from a totals dict.
* :func:`damage_coeffs` — integer-scaled ``(coeffs, constant)`` so CP-SAT can
  build the objective as ``sum(coeffs[dim] * total[dim]) + constant`` in pure
  integer arithmetic (``DAMAGE_SCALE`` clears the ``/100``).
"""

from __future__ import annotations

from app.config import BASE_GENERIQUE, DAMAGE_SCALE

# dims that enter the multiplicative coefficient (% terms / characteristic)
COEFF_DIMS_BASE = ["puissance", "pct_do"]

assert DAMAGE_SCALE % 100 == 0, "DAMAGE_SCALE must be a multiple of 100 for integer scaling"
_PCT_COEF = BASE_GENERIQUE * DAMAGE_SCALE // 100   # coef applied to a +1 % term
_FLAT_COEF = DAMAGE_SCALE                          # coef applied to +1 fixed damage
_CONST = BASE_GENERIQUE * DAMAGE_SCALE             # the "1 *" base term, scaled


def damage_coeffs(
    carac: str,
    do_elem: str,
    profile_dims: tuple[str, ...] = (),
) -> tuple[dict[str, int], int]:
    """Integer-scaled linear damage for one element.

    ``profile_dims`` are extra ``%`` dimensions that enter the multiplicative
    coefficient (e.g. ``pct_do_melee`` for a melee profile). Empty = generic.

    Returns ``(coeffs, constant)`` where the (scaled) damage equals
    ``sum(coeffs[dim] * total[dim] for dim) + constant``.
    """
    coeffs: dict[str, int] = {}
    coeffs[carac] = coeffs.get(carac, 0) + _PCT_COEF
    for d in (*COEFF_DIMS_BASE, *profile_dims):
        coeffs[d] = coeffs.get(d, 0) + _PCT_COEF
    coeffs["do_fixe"] = coeffs.get("do_fixe", 0) + _FLAT_COEF
    coeffs[do_elem] = coeffs.get(do_elem, 0) + _FLAT_COEF
    return coeffs, _CONST


def theoretical_damage(
    totals: dict[str, int | float],
    carac: str,
    do_elem: str,
    profile_dims: tuple[str, ...] = (),
    *,
    crit: bool = False,
) -> float:
    """Human-scale theoretical damage of a single hit for KPI display."""
    pct = (
        totals.get(carac, 0)
        + totals.get("puissance", 0)
        + totals.get("pct_do", 0)
        + sum(totals.get(d, 0) for d in profile_dims)
    )
    flat = totals.get("do_fixe", 0) + totals.get(do_elem, 0)
    if crit:
        flat += totals.get("do_critiques", 0)
    return BASE_GENERIQUE * (1 + pct / 100) + flat


def multi_damage(
    totals: dict[str, int | float],
    elements: list[tuple[str, str]],
    profile_dims: tuple[str, ...] = (),
    *,
    crit: bool = False,
) -> float:
    """Average theoretical damage across several (carac, do_elem) pairs."""
    if not elements:
        return 0.0
    return sum(
        theoretical_damage(totals, carac, do_elem, profile_dims, crit=crit)
        for carac, do_elem in elements
    ) / len(elements)
