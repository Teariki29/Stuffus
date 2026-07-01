"""Parse DofusDB ``criterions`` strings into a structured condition tree.

Grammar (observed in the live data)::

    expr   := or
    or     := and ( '|' and )*
    and    := atom ( '&' atom )*
    atom   := '(' expr ')' | CODE OP VALUE
    CODE   := [A-Za-z]+              e.g. CS, CI, PL, PJ …
    OP     := '>' | '<' | '=' | '!'
    VALUE  := [^&|()]+               number, optionally 'n,param'

Only criterions that reference a characteristic the solver actually controls are
turned into real comparisons. Every other code (level/quest/alignment/server/…)
is mapped to an always-true node: a stuff optimiser must not exclude an item
because of, say, a quest the player may already have done. (Refined in P6.)

Output node shapes::

    {"op": "and"|"or", "children": [...]}
    {"op": "cmp", "dim": "force", "operator": ">", "value": 200}
    {"op": "true", "code": "PL"}     # recognised but ignored
"""

from __future__ import annotations

import re

# criterion code -> controllable stat dimension. Decoded against dofusdude's
# resolved conditions (this is only a *fallback*; the structured dofusdude
# conditions are the primary source — see parse_dofusdude_condition).
CODE_TO_DIM: dict[str, str] = {
    "CV": "vitalite",
    "CS": "force",       # NB: CS is Force, not Sagesse
    "CW": "sagesse",
    "CC": "chance",
    "CA": "agilite",
    "CI": "intelligence",
    "CP": "pa",
    "CM": "pm",
    "Pk": "nb_panoplies",   # "< N bonus de panoplies" (build-determined)
    # other P-/Q-/S-/O-codes (PL niveau, quêtes, alignement, abonnement, kamas…)
    # are external player state the build can't satisfy -> unmapped (assumed met).
}

_TOKEN_RE = re.compile(r"\s*(\(|\)|&|\||[A-Za-z]+[<>=!][^&|()]+)")
_ATOM_RE = re.compile(r"([A-Za-z]+)([<>=!])(.+)")


class _Parser:
    def __init__(self, text: str):
        self.tokens = self._tokenize(text)
        self.pos = 0

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        tokens: list[str] = []
        i = 0
        while i < len(text):
            m = _TOKEN_RE.match(text, i)
            if not m:
                i += 1
                continue
            tokens.append(m.group(1))
            i = m.end()
        return tokens

    def _peek(self) -> str | None:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def _next(self) -> str | None:
        tok = self._peek()
        if tok is not None:
            self.pos += 1
        return tok

    def parse(self) -> dict | None:
        if not self.tokens:
            return None
        node = self._parse_or()
        return node

    def _parse_or(self) -> dict:
        children = [self._parse_and()]
        while self._peek() == "|":
            self._next()
            children.append(self._parse_and())
        if len(children) == 1:
            return children[0]
        return {"op": "or", "children": children}

    def _parse_and(self) -> dict:
        children = [self._parse_atom()]
        while self._peek() == "&":
            self._next()
            children.append(self._parse_atom())
        if len(children) == 1:
            return children[0]
        return {"op": "and", "children": children}

    def _parse_atom(self) -> dict:
        tok = self._next()
        if tok == "(":
            node = self._parse_or()
            if self._peek() == ")":
                self._next()
            return node
        if tok is None:
            return {"op": "true", "code": None}
        return self._atom_from(tok)

    @staticmethod
    def _atom_from(tok: str) -> dict:
        m = _ATOM_RE.match(tok)
        if not m:
            return {"op": "true", "code": tok}
        code, operator, raw_value = m.group(1), m.group(2), m.group(3)
        dim = CODE_TO_DIM.get(code)
        if dim is None:
            return {"op": "true", "code": code}
        # value may carry a ",param"; the stat comparison only uses the number
        num_part = raw_value.split(",", 1)[0].strip()
        try:
            value = int(num_part)
        except ValueError:
            return {"op": "true", "code": code}
        return {"op": "cmp", "dim": dim, "operator": operator, "value": value}


def parse_criterion(text: str | None) -> dict | None:
    """Parse a criterion string into a condition tree (or ``None`` if empty)."""
    if not text:
        return None
    return _Parser(text).parse()


# --------------------------------------------------------------------------- #
# dofusdude structured conditions (preferred source)
# --------------------------------------------------------------------------- #
# Condition element *name* -> controllable stat dimension. Anything not here
# (Kamas, alignement, abonnement, quêtes, bonus de panoplies, niveau joueur…) is
# external player state the optimiser cannot satisfy from the build, so it is
# treated as always-true (assumed met). Mapping by name is robust — it sidesteps
# DofusDB's cryptic 2-letter codes entirely.
CONDITION_ELEMENT_TO_DIM: dict[str, str] = {
    "Force": "force",
    "Vitalité": "vitalite",
    "Sagesse": "sagesse",
    "Chance": "chance",
    "Agilité": "agilite",
    "Intelligence": "intelligence",
    "PA": "pa",
    "PM": "pm",
    "Portée": "po",
    "Puissance": "puissance",
    # build-determined meta condition: number of active set bonuses. Handled
    # specially by the model (not a stat in STATS) — see BuildModel.total().
    "Bonus de panoplies": "nb_panoplies",
}

# pseudo-dimension for the active-set-bonus count condition (e.g. trophies that
# require "< 3 bonus de panoplies"). Resolved by the model, not a real stat.
PANOPLIE_COUNT_DIM = "nb_panoplies"


def parse_dofusdude_condition(node: dict | None) -> dict | None:
    """Convert a dofusdude condition tree into the internal condition tree.

    Leaf:    ``{is_operand: true, condition: {operator, int_value, element:{name}}}``
    Branch:  ``{is_operand: false, relation: "and"|"or", children: [...]}``
    """
    if not node:
        return None
    if node.get("is_operand"):
        cond = node.get("condition") or {}
        element = (cond.get("element") or {}).get("name")
        dim = CONDITION_ELEMENT_TO_DIM.get(element)
        if dim is None:
            return {"op": "true", "code": element}
        return {
            "op": "cmp",
            "dim": dim,
            "operator": cond.get("operator", "="),
            "value": int(cond.get("int_value", 0)),
        }
    children = [parse_dofusdude_condition(c) for c in node.get("children", [])]
    children = [c for c in children if c is not None]
    if not children:
        return None
    if len(children) == 1:
        return children[0]
    relation = node.get("relation", "and")
    return {"op": relation, "children": children}


def collect_stat_constraints(node: dict | None) -> list[dict]:
    """Flatten the ``cmp`` leaves that reference controllable stats.

    Useful for a quick AND-only view; the full tree (with OR) is what the model
    consumes. Returns ``[{dim, operator, value}, …]``.
    """
    out: list[dict] = []
    if not node:
        return out
    op = node.get("op")
    if op == "cmp":
        out.append({"dim": node["dim"], "operator": node["operator"], "value": node["value"]})
    elif op in ("and", "or"):
        for child in node["children"]:
            out.extend(collect_stat_constraints(child))
    return out
