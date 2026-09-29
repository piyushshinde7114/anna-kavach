"""End-to-end API flow: recommend -> PDF -> trace -> batch -> feedback -> calibration."""
import os
import tempfile

os.environ["ANNAKAVACH_DB"] = os.path.join(tempfile.mkdtemp(), "t.db")
from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402

c = TestClient(app)


def test_meta():
    m = c.get("/api/meta").json()
    assert m["counts"]["foods"] >= 20 and m["counts"]["films"] >= 12


def test_dry_flow_with_trace_and_feedback():
    r = c.post("/api/recommend", json=dict(food_id="banana_chips", pack=dict(weight_g=200, width_cm=15, height_cm=22),
                                            target_days=180, route=dict(origin="Kochi", destination="Delhi", month=4)))
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["dry"]["picks"]["green"]
    pid, code = d["project_id"], d["trace_code"]
    pdf = c.get(f"/api/projects/{pid}/pdf")
    assert pdf.status_code == 200 and pdf.content[:4] == b"%PDF"
    assert c.post(f"/api/trace/{code}/batches", json=dict(lot="L-001", packed_on="2026-09-01", quantity=500)).status_code == 200
    fb = c.post(f"/api/trace/{code}/feedback", json=dict(observed_days=150, outcome="soggy", notes="humid monsoon store"))
    assert fb.json()["calibration"]["n"] == 1
    t = c.get(f"/api/trace/{code}").json()
    assert t["batches"][0]["lot"] == "L-001" and len(t["feedback"]) == 1


def test_produce_flow_and_stress():
    r = c.post("/api/recommend", json=dict(food_id="mango", fill_kg=1, legs=[
        dict(name="Packhouse", hours=2, temp_c=25), dict(name="Reefer", hours=36, temp_c=13), dict(name="Retail", hours=48, temp_c=30)]))
    d = r.json()
    assert d["map"]["map_works"] and d["map"]["vent_at"] == 38
    s = c.post(f"/api/projects/{d['project_id']}/simulate", json=[
        dict(name="Packhouse", hours=2, temp_c=25), dict(name="Reefer", hours=36, temp_c=24), dict(name="Retail", hours=48, temp_c=30)]).json()
    assert s["sim"]["injury_h"] > 0  # hot truck breaks the design


def test_custom_food_and_errors():
    r = c.post("/api/recommend", json=dict(custom=dict(name="Jackfruit chips", mi=3, fat=30, protein=3, carb=60),
                                            pack=dict(weight_g=150, width_cm=14, height_cm=20), target_days=120))
    assert r.status_code == 200 and r.json()["estimate"]["neighbours"]
    assert c.post("/api/recommend", json=dict(food_id="mango")).status_code == 422
    assert c.post("/api/intake", json=dict(text="500g peanuts 6 months Pune to Patna")).json()["parsed"]["food_id"] == "peanuts_roasted"
