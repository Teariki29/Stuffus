"""Map dofusdude effect ``type.name`` -> canonical stat dimension.

Built data-driven from the 98 distinct effect names present in the live dump.
Anything not listed here is intentionally ignored (cosmetic/meta lines, weapon
spell metadata such as the ``: …`` prefixed entries, push/trap damage, etc.).

The important subtlety (plan): a *weapon* carries its own hit-damage lines which
must NOT be counted as fixed-damage stats. In dofusdude these use a **lowercase**
"dommages/vol/soins <element>" name, whereas the fixed-damage *stat* uses the
**capitalised** "Dommage <element>". Hit lines are routed to ``weapon_json``.
"""

from __future__ import annotations

# effect type name -> canonical dimension
EFFECT_TO_DIM: dict[str, str] = {
    # primary characteristics
    "Vitalité": "vitalite",
    "Sagesse": "sagesse",
    "Force": "force",
    "Intelligence": "intelligence",
    "Chance": "chance",
    "Agilité": "agilite",
    "PA": "pa",
    "PM": "pm",
    "Portée": "po",
    # damage
    "Puissance": "puissance",
    "Dommage": "do_fixe",
    "Dommage Terre": "do_terre",
    "Dommage Feu": "do_feu",
    "Dommage Eau": "do_eau",
    "Dommage Air": "do_air",
    "Dommage Neutre": "do_neutre",
    "Dommage Critiques": "do_critiques",
    "% Dommages d'armes": "pct_do_armes",
    "% Dommages distance": "pct_do_distance",
    "% Dommages aux sorts": "pct_do_sorts",
    "% Dommages mêlée": "pct_do_melee",
    # crits / resistances
    "% Critique": "cc",
    "% Résistance Terre": "res_terre",
    "% Résistance Feu": "res_feu",
    "% Résistance Eau": "res_eau",
    "% Résistance Air": "res_air",
    "% Résistance Neutre": "res_neutre",
    "Résistance Terre": "res_fixe_terre",
    "Résistance Feu": "res_fixe_feu",
    "Résistance Eau": "res_fixe_eau",
    "Résistance Air": "res_fixe_air",
    "Résistance Neutre": "res_fixe_neutre",
    # misc
    "Soin": "do_soins",
    "Prospection": "prospection",
    "Pod": "pods",
    "Initiative": "initiative",
    "Tacle": "tacle",
    "Fuite": "fuite",
    "Invocation": "invocations",
    "Esquive PA": "esquive_pa",
    "Esquive PM": "esquive_pm",
    "Retrait PA": "retrait_pa",
    "Retrait PM": "retrait_pm",
}

# lowercase weapon hit-damage / life-steal / heal lines -> excluded from stats
WEAPON_HIT_NAMES: set[str] = {
    "dommages Neutre",
    "dommages Terre",
    "dommages Feu",
    "dommages Eau",
    "dommages Air",
    "dommages du meilleur élément",
    "vol Neutre",
    "vol Terre",
    "vol Feu",
    "vol Eau",
    "vol Air",
    "vol du meilleur élément",
    "soins Feu",
}

# element keyword carried by a weapon hit line, for weapon_json display
WEAPON_HIT_ELEMENT: dict[str, str] = {
    "dommages Neutre": "neutre",
    "dommages Terre": "terre",
    "dommages Feu": "feu",
    "dommages Eau": "eau",
    "dommages Air": "air",
    "vol Neutre": "neutre",
    "vol Terre": "terre",
    "vol Feu": "feu",
    "vol Eau": "eau",
    "vol Air": "air",
    "soins Feu": "feu",
    "dommages du meilleur élément": "best",
    "vol du meilleur élément": "best",
}


def roll_value(effect: dict) -> int:
    """Jet parfait (max roll) of a dofusdude effect.

    * fixed value  -> ``ignore_int_max`` true, value is ``int_minimum``
    * ranged value -> value is ``int_maximum``
    """
    if effect.get("ignore_int_max"):
        return int(effect.get("int_minimum", 0))
    imax = effect.get("int_maximum", 0)
    if imax in (0, None):
        return int(effect.get("int_minimum", 0))
    return int(imax)
