"""Request models (plan §7)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from app.solver.stats import STAT_INDEX

StuffType = Literal["force", "intel", "chance", "agi", "multi", "sagesse"]
Element = Literal["terre", "feu", "eau", "air"]
Operator = Literal[">=", "<=", ">", "<", "==", "!=", "="]
DamageProfile = Literal["generique", "melee", "distance", "sorts", "armes"]


class Constraint(BaseModel):
    dim: str
    op: Operator
    value: int

    @field_validator("dim")
    @classmethod
    def _known_dim(cls, v: str) -> str:
        if v not in STAT_INDEX:
            raise ValueError(f"unknown stat dimension: {v!r}")
        return v


class OptimizeRequest(BaseModel):
    stuff_type: StuffType
    level: int = Field(ge=1, le=200)
    elements: list[Element] = Field(default_factory=list)
    damage_profile: DamageProfile = "generique"
    constraints: list[Constraint] = Field(default_factory=list)
    tiebreak_weights: dict[str, int] = Field(default_factory=dict)
    allocate_points: bool = True
    obtainable_only: bool = True
    banned_ids: list[int] = Field(default_factory=list)
    time_limit: float = Field(default=15.0, ge=1.0, le=60.0)

    @model_validator(mode="after")
    def _check_multi(self) -> OptimizeRequest:
        if self.stuff_type == "multi" and len(self.elements) < 2:
            raise ValueError("multi stuff_type requires at least 2 elements")
        return self

    @field_validator("tiebreak_weights")
    @classmethod
    def _known_weight_dims(cls, v: dict[str, int]) -> dict[str, int]:
        for dim in v:
            if dim not in STAT_INDEX:
                raise ValueError(f"unknown tiebreak dimension: {dim!r}")
        return v
