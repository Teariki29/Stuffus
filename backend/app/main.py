"""FastAPI application entry point."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router

app = FastAPI(
    title="Dofus Stuff Optimizer",
    version="0.1.0",
    description=(
        "Retourne le build optimal prouvé sous contraintes. "
        "Données issues de DofusDB / dofusdude (Ankama). Usage non commercial."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
def root():
    return {"name": "dofus-optimizer", "docs": "/docs"}
