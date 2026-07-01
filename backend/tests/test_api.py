"""P10 validation: the /optimize endpoint honours the API contract."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["items"] > 1000


def test_optimize_contract():
    r = client.post(
        "/optimize",
        json={
            "stuff_type": "force",
            "level": 200,
            "constraints": [
                {"dim": "pa", "op": ">=", "value": 11},
                {"dim": "pm", "op": ">=", "value": 6},
            ],
            "time_limit": 15,
        },
    )
    assert r.status_code == 200
    d = r.json()
    assert d["status"] in ("OPTIMAL", "FEASIBLE")
    assert d["totals"]["pa"] >= 11 and d["totals"]["pm"] >= 6
    assert d["kpi"]["damage_normal"] > 0
    assert len(d["items"]) > 0


def test_multi_requires_two_elements():
    r = client.post("/optimize", json={"stuff_type": "multi", "level": 200, "elements": ["terre"]})
    assert r.status_code == 422


def test_unknown_dim_rejected():
    r = client.post(
        "/optimize",
        json={"stuff_type": "force", "level": 200,
              "constraints": [{"dim": "bogus", "op": ">=", "value": 1}]},
    )
    assert r.status_code == 422


def test_damage_profile_and_set_bonus_and_exclusions():
    r = client.post(
        "/optimize",
        json={
            "stuff_type": "force",
            "level": 200,
            "damage_profile": "distance",
            "constraints": [{"dim": "pa", "op": ">=", "value": 11}],
            "time_limit": 15,
        },
    )
    assert r.status_code == 200
    d = r.json()
    assert d["status"] in ("OPTIMAL", "FEASIBLE")
    # active sets carry their tier bonus
    if d["active_sets"]:
        assert all("bonus" in s for s in d["active_sets"])
        assert any(s["bonus"] for s in d["active_sets"])
    # GM / non-obtainable gear must never appear
    names = [it["name"] for it in d["items"]]
    assert not any("(MJ)" in n or "Jarbo" in n for n in names)


def test_bad_damage_profile_rejected():
    r = client.post(
        "/optimize",
        json={"stuff_type": "force", "level": 200, "damage_profile": "lightsaber"},
    )
    assert r.status_code == 422
