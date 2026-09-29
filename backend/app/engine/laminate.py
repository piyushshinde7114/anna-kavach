"""Laminate composer: builds 1-3 layer structures from the film library and scores their properties."""
from itertools import product
from .physics import series

OUTERS = [None, "PET12", "BOPP20", "BOPA15", "KRAFT60", "AlOxPET12", "mPET12"]
BARRIERS = [None, "mPET12", "mBOPP20", "AL9"]
SEALANTS = ["LDPE50", "LLDPE50", "CPP30", "EVOHPE60", "mBOPP20"]
MONOS = [["LDPE50"], ["HDPE25", "LDPE25"], ["PLA25"], ["CPP30"]]


def _valid(outer, barrier, sealant):
    ids = [x for x in (outer, barrier, sealant) if x]
    if len(set(ids)) != len(ids):
        return False
    if sealant == "mBOPP20":  # heat-seal met-BOPP: only as the mono-PP pair BOPP / met-BOPP
        return outer == "BOPP20" and barrier is None
    if barrier == "AL9" and outer not in ("PET12", "BOPA15", "KRAFT60"):
        return False  # foil needs a protective outer web
    if barrier == "mBOPP20" and outer not in ("BOPP20", "PET12"):
        return False
    if barrier == "mPET12" and outer in ("mPET12", "AlOxPET12"):
        return False
    if outer == "mPET12" and barrier is not None:
        return False
    if outer is None and barrier is not None:
        return False
    if outer == "KRAFT60" and sealant not in ("LDPE50", "LLDPE50"):
        return False
    if outer == "BOPA15" and sealant == "CPP30":
        return False
    return True


def all_structures():
    out = [m for m in MONOS]
    for o, b, s in product(OUTERS, BARRIERS, SEALANTS):
        if o is None and b is None:
            continue  # sealant alone is covered by MONOS
        if _valid(o, b, s):
            out.append([x for x in (o, b, s) if x])
    return out


def eco_class(layers):
    fams = {f["family"] for f in layers}
    if fams == {"PLA"}:
        return dict(rank=1, label="Compostable", detail="Needs IS/ISO 17088 test report and CPCB certificate", epr="Compostable")
    if "AL" in fams:
        return dict(rank=3, label="Plastic + foil", detail="Hard to recycle; EPR Category III", epr="Cat III")
    if "PAPER" in fams:
        return dict(rank=3, label="Paper + plastic", detail="Composite; EPR Category III", epr="Cat III")
    if len(fams) == 1 or fams <= {"PE", "PE+EVOH"}:
        fam = next(iter(fams)).replace("+EVOH", "")
        return dict(rank=0, label=f"Mono-{fam}", detail=f"Single-polymer {fam} stream; EPR Category II", epr="Cat II")
    return dict(rank=2, label="Multi-polymer", detail="Mixed plastics, hard to recycle; EPR Category II", epr="Cat II")


def build(ids, films, lam_cost):
    L = [films[i] for i in ids]
    bonds = len(L) - 1
    grams_m2 = sum(f["um"] * f["density"] for f in L)  # g/m2 (um x g/cm3)
    co2e_m2 = sum(f["um"] * f["density"] * f["co2e"] for f in L) / 1000  # kg CO2e per m2
    cost = [sum(f["cost_m2"][j] for f in L) + bonds * lam_cost[j] for j in (0, 1)]
    return dict(
        ids=ids, name=" / ".join(f["name"].split(" (")[0] for f in L),
        layers=[dict(id=f["id"], name=f["name"], family=f["family"], um=f["um"], opaque=f["opaque"]) for f in L],
        wvtr=[series([f["wvtr"][0] for f in L]), series([f["wvtr"][1] for f in L])],
        otr=[series([f["otr"][0] for f in L]), series([f["otr"][1] for f in L])],
        seal=L[-1]["seal"], opaque=any(f["opaque"] for f in L), tmin=max(f["tmin"] for f in L),
        tmax=min(f["tmax"] for f in L), grease=L[-1]["grease"], cost_m2=cost, grams_m2=grams_m2, co2e_m2=co2e_m2,
        eco=eco_class(L), vacuum_ok=any(f["family"] in ("PA", "PE+EVOH") for f in L) or "AL9" in ids or "mPET12" in ids,
    )
