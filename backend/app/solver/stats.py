"""Canonical stat dimensions.

The ORDER of ``STATS`` is frozen once and for all: every item vector, the race
base, the scroll bonuses and the set bonuses are projected onto this exact
ordering. Indices into a stat vector are derived from :data:`STAT_INDEX`.

If you ever add a dimension, append it at the END so existing data stays valid.
"""

from __future__ import annotations

STATS: list[str] = [
    # --- primary characteristics --------------------------------------------
    "vitalite",
    "pa",
    "pm",
    "po",
    "force",
    "intelligence",
    "chance",
    "agilite",
    "sagesse",
    # --- damage -------------------------------------------------------------
    "puissance",
    "do_fixe",          # generic fixed damage ("Dommages")
    "do_terre",         # fixed elemental damage
    "do_feu",
    "do_eau",
    "do_air",
    "do_neutre",
    "pct_do",           # % damage ("% Dommages")
    "pct_do_melee",
    "pct_do_distance",
    "pct_do_sorts",
    "pct_do_armes",
    "do_critiques",     # fixed damage applied only on a critical hit
    # --- crits / resistances (constraints + display) ------------------------
    "cc",               # % critical hit
    "res_terre",        # % resistances
    "res_feu",
    "res_eau",
    "res_air",
    "res_neutre",
    "res_fixe_terre",   # flat resistances
    "res_fixe_feu",
    "res_fixe_eau",
    "res_fixe_air",
    "res_fixe_neutre",
    # --- misc ---------------------------------------------------------------
    "soins",            # % heals ("% Soins")
    "do_soins",         # flat heal bonus ("Soins")
    "prospection",
    "pods",
    "initiative",
    "tacle",
    "fuite",
    "invocations",
    "esquive_pa",       # dodge AP / withdrawal
    "esquive_pm",
    "retrait_pa",
    "retrait_pm",
]

STAT_INDEX: dict[str, int] = {name: i for i, name in enumerate(STATS)}
N_STATS: int = len(STATS)


def zero_vector() -> list[int]:
    """Return a fresh zero stat vector of the canonical length."""
    return [0] * N_STATS


def vector_from_dict(d: dict[str, int]) -> list[int]:
    """Project a ``{dim: value}`` mapping onto the canonical ordered vector."""
    vec = zero_vector()
    for dim, val in d.items():
        idx = STAT_INDEX.get(dim)
        if idx is not None:
            vec[idx] += int(val)
    return vec


def dict_from_vector(vec: list[int]) -> dict[str, int]:
    """Inverse of :func:`vector_from_dict`, dropping zero entries."""
    return {STATS[i]: vec[i] for i in range(N_STATS) if vec[i] != 0}


# The six characteristics whose points the solver may allocate.
ALLOCATABLE_CARACS: list[str] = [
    "vitalite",
    "force",
    "intelligence",
    "chance",
    "agilite",
    "sagesse",
]

# Mapping: stuff type -> (characteristic dimension, fixed elemental damage dim).
STUFF_TYPE_MAP: dict[str, tuple[str, str]] = {
    "force": ("force", "do_terre"),
    "intel": ("intelligence", "do_feu"),
    "chance": ("chance", "do_eau"),
    "agi": ("agilite", "do_air"),
}

# Element -> (characteristic, fixed elemental damage, % res dim). Used for multi.
ELEMENT_MAP: dict[str, tuple[str, str, str]] = {
    "terre": ("force", "do_terre", "res_terre"),
    "feu": ("intelligence", "do_feu", "res_feu"),
    "eau": ("chance", "do_eau", "res_eau"),
    "air": ("agilite", "do_air", "res_air"),
}
