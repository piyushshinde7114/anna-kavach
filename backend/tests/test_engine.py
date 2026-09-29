"""Engine checks against hand calculations and known behaviour."""
import math
import pytest
from app.data import seed
from app.engine import physics, laminate, dry, mapsim, intake
from app.engine.profiler import Estimator, failure_modes

FILMS = {f["id"]: f for f in seed.FILMS}
FOODS = {f["id"]: f for f in seed.FOODS}
FLAT = [dict(T=30.0, RH=0.80)] * 12


def test_saturation_pressure():
    assert physics.psat_kpa(25) == pytest.approx(3.17, abs=0.02)
    assert physics.psat_kpa(38) == pytest.approx(6.63, abs=0.05)


def test_layers_in_series():
    assert physics.series([10, 10]) == pytest.approx(5)
    assert physics.series([1, 1000]) == pytest.approx(0.999, abs=1e-3)


def test_banana_chip_moisture_budget_matches_hand_calculation():
    # 200 g, 2.5 -> 5 % db, 15 x 22 cm pouch, 180 d at 30 C / 80 % RH, aw 0.30: deck slide 4 says WVTR <= 1.15
    r = dry.evaluate(FOODS["banana_chips"], dict(weight_g=200, width_cm=15, height_cm=22), 180, FLAT, 0, FILMS,
                     seed.LAMINATION_COST_M2, seed.O2_RULES)
    assert r["requirement"]["wvtr_max"] == pytest.approx(1.15, abs=0.02)
    assert r["calc"]["water_allowed_g"] == pytest.approx(4.88, abs=0.02)


def test_plain_ldpe_fails_and_mono_pp_passes_for_chips():
    r = dry.evaluate(FOODS["banana_chips"], dict(weight_g=200, width_cm=15, height_cm=22), 180, FLAT, 0, FILMS,
                     seed.LAMINATION_COST_M2, seed.O2_RULES)
    by = {tuple(c["ids"]): c for c in r["candidates"]}
    assert not by[("LDPE50",)]["pass"]
    assert by[("LDPE50",)]["life"]["p50"] < 40
    assert by[("BOPP20", "mBOPP20")]["pass"]
    assert r["picks"]["green"] == ["BOPP20", "mBOPP20"]


def test_composer_builds_many_valid_structures():
    s = laminate.all_structures()
    assert len(s) >= 30
    assert ["PET12", "AL9", "LDPE50"] in s
    assert ["BOPP20", "AL9", "LDPE50"] not in s  # foil needs PET / nylon / paper outer


def test_mango_needs_vent_rule_and_then_has_no_injury():
    legs = [dict(name="Packhouse", hours=2, temp_c=25), dict(name="Reefer", hours=36, temp_c=13), dict(name="Retail", hours=48, temp_c=30)]
    m = mapsim.evaluate(FOODS["mango"], legs, FILMS, 1.0)
    assert m["map_works"]
    assert m["sealed"]["injury_h"] > 10  # sealed MAP fails once the cold chain ends
    assert m["vent_at"] == pytest.approx(38)
    assert m["final"]["injury_h"] < 0.5
    assert m["baseline"]["sim"]["injury_h"] > 40  # plain sealed bag goes anaerobic


def test_tomato_map_not_recommended():
    legs = [dict(name="Packhouse", hours=2, temp_c=25), dict(name="Reefer", hours=30, temp_c=12), dict(name="Retail", hours=48, temp_c=30)]
    assert not mapsim.evaluate(FOODS["tomato"], legs, FILMS, 1.0)["map_works"]


def test_intake_parses_english_and_hindi():
    cities = list(seed.CITIES)
    p = intake.parse("200 g banana chips 6 months Kochi to Delhi in May", seed.FOODS, cities, seed.CITY_HI)["parsed"]
    assert p["food_id"] == "banana_chips" and p["weight_g"] == 200 and p["target_days"] == 182
    assert p["origin"] == "Kochi" and p["destination"] == "Delhi" and p["month"] == 4
    h = intake.parse("1 किलो आम रत्नागिरी से दिल्ली", seed.FOODS, cities, seed.CITY_HI)["parsed"]
    assert h["food_id"] == "mango" and h["weight_g"] == 1000 and h["origin"] == "Ratnagiri" and h["destination"] == "Delhi"


def test_estimator_borrows_from_similar_foods():
    e = Estimator(seed.FOODS).estimate(dict(mi=2.5, fat=33, protein=3, carb=58))
    assert e["neighbours"][0]["id"] in ("banana_chips", "potato_chips", "namkeen")
    assert e["o2"] == "high" and e["confidence"] > 0.5


def test_failure_modes():
    modes = {m["mode"] for m in failure_modes(FOODS["paneer"])}
    assert "microbial" in modes
    assert {m["mode"] for m in failure_modes(FOODS["banana_chips"])} >= {"moisture gain", "oxidation"}
