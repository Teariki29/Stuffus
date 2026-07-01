"""Game constants and tunables.

⚠️  These values reflect classic Dofus 2/3 rules. They are gathered here on
purpose (plan §5.6 / §10): the exact thresholds may have shifted with Dofus 3
(Unity) and should be re-checked against the live game. Nothing here is hard
coded deeper in the codebase — change a value once, here.
"""

from __future__ import annotations

# --------------------------------------------------------------------------- #
# Damage formula
# --------------------------------------------------------------------------- #
# Generic spell base used for the theoretical-damage objective. Per the frozen
# decisions we optimise a generic coefficient, not a specific spell. The value
# only scales the displayed KPI; it never changes which build is optimal.
BASE_GENERIQUE: int = 100

# CP-SAT works in integers. The damage expression carries /100 terms, so we
# scale the whole objective by this factor to stay in integer arithmetic.
# Must be a multiple of 100; kept small so objective coefficients stay modest
# (large coefficients blow up CP-SAT's LP relaxation and slow the search).
DAMAGE_SCALE: int = 100

# --------------------------------------------------------------------------- #
# Characteristic point allocation
# --------------------------------------------------------------------------- #
# Capital of characteristic points available at a given level: 5 per level
# gained after level 1.
def points_for_level(level: int) -> int:
    return max(0, (level - 1) * 5)


# Cost tranches for the four elemental characteristics (force, intelligence,
# chance, agilite). Each tranche is (width_in_stat_points, cost_per_point).
# 1:1 up to 100, then 2:1, 3:1, 4:1, 5:1.
ELEMENTAL_TRANCHES: list[tuple[int, int]] = [
    (100, 1),
    (100, 2),
    (100, 3),
    (100, 4),
    (100, 5),
]

# Vitalité: 1 characteristic point -> 1 vitalité, no tranches.
VITALITE_TRANCHES: list[tuple[int, int]] = [(10_000, 1)]

# Sagesse: 3 characteristic points -> 1 sagesse.
SAGESSE_TRANCHES: list[tuple[int, int]] = [(10_000, 3)]

TRANCHES_BY_CARAC: dict[str, list[tuple[int, int]]] = {
    "force": ELEMENTAL_TRANCHES,
    "intelligence": ELEMENTAL_TRANCHES,
    "chance": ELEMENTAL_TRANCHES,
    "agilite": ELEMENTAL_TRANCHES,
    "vitalite": VITALITE_TRANCHES,
    "sagesse": SAGESSE_TRANCHES,
}

# --------------------------------------------------------------------------- #
# Race / base character
# --------------------------------------------------------------------------- #
# Flat life every character has before vitalité is counted (class-independent
# approximation). 1 vitalité == 1 life.
BASE_LIFE: int = 55

# Base action / movement points granted to every character.
BASE_PA: int = 6
BASE_PM: int = 3
BASE_PO: int = 0
BASE_CC: int = 0  # base critical chance comes from spells/weapons, not the char

# --------------------------------------------------------------------------- #
# Slots
# --------------------------------------------------------------------------- #
SLOTS_SIMPLES: list[str] = [
    "coiffe",
    "cape",
    "amulette",
    "ceinture",
    "bottes",
    "bouclier",
    "arme",
    "familier",
]
MAX_ANNEAUX = 2
MAX_DOFUS_TROPHEE = 6

ALL_SLOTS: list[str] = SLOTS_SIMPLES + ["anneau", "dofus", "trophee"]

# dofusdude item ``type.name`` -> canonical slot. Weapon types all collapse to
# "arme". Unknown types are dropped during normalisation (and logged).
TYPE_TO_SLOT: dict[str, str] = {
    # armour / accessories
    "Chapeau": "coiffe",
    "Cape": "cape",
    "Sac à dos": "cape",
    "Amulette": "amulette",
    "Anneau": "anneau",
    "Ceinture": "ceinture",
    "Bottes": "bottes",
    "Bouclier": "bouclier",
    "Dofus": "dofus",
    "Prysmaradite": "dofus",
    "Trophée": "trophee",
    # the single pet / mount slot (familier, montilier or mount)
    "Familier": "familier",
    "Montilier": "familier",
    "Monture": "familier",
    "Compagnon": "familier",
    "Dragodinde": "familier",
    "Muldo": "familier",
    "Volkorne": "familier",
    # weapons
    "Épée": "arme",
    "Hache": "arme",
    "Dague": "arme",
    "Bâton": "arme",
    "Marteau": "arme",
    "Pelle": "arme",
    "Arc": "arme",
    "Baguette": "arme",
    "Faux": "arme",
    "Pioche": "arme",
    "Lance": "arme",
    "Outil": "arme",
    "Arme magique": "arme",
}

# Types deliberately excluded (NPC perceptor gear, inactive mount certificates):
# anything containing these substrings is dropped during normalisation.
EXCLUDED_TYPE_SUBSTRINGS: tuple[str, ...] = ("Percepteur", "Certificat")

# Items deliberately excluded by name (GM / non-obtainable gear): any item whose
# name contains one of these substrings is dropped during normalisation.
EXCLUDED_NAME_SUBSTRINGS: tuple[str, ...] = ("(MJ)", "Maître Jarbo")

# --------------------------------------------------------------------------- #
# Obtainability
# --------------------------------------------------------------------------- #
# DofusDB has no clean "obtainable" flag. Empirically, bit 1024 of m_flags marks
# an item as *échangeable* (tradeable on the marketplace), which is the best
# available proxy for "a player can get this": all GM/NPC/test/joke items lack
# it. The downside is that a handful of *bound* but real items also lack it —
# notably several Dofus — so we always keep the slots in OBTAINABLE_KEEP_SLOTS
# and any id in OBTAINABLE_ALLOWLIST. This is exposed as a toggle in the API
# (``obtainable_only``); turn it off to consider every item in the database.
OBTAINABLE_FLAG_BIT: int = 1024
OBTAINABLE_KEEP_SLOTS: frozenset[str] = frozenset({"dofus"})
OBTAINABLE_ALLOWLIST: frozenset[int] = frozenset()  # extra ankama ids to keep

# Type names whose items are weapons (carry their own hit damage lines that
# must NOT be counted as fixed-damage stats).
WEAPON_TYPE_NAMES: set[str] = {
    "Épée", "Hache", "Dague", "Bâton", "Marteau", "Pelle",
    "Arc", "Baguette", "Faux", "Pioche", "Lance", "Outil", "Arme magique",
}
