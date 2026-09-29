"""M1 food profiler: rules for failure modes + a k-nearest-neighbour estimator for foods not in the library.

The estimator never invents a food; it borrows properties from the most similar curated foods,
weights them by similarity, and reports a confidence. Low confidence asks the user to measure.
"""
import numpy as np
from sklearn.neighbors import NearestNeighbors

FEATURES = ["mi", "fat", "protein", "carb"]
SCALE = np.array([5.0, 20.0, 10.0, 25.0])  # typical spread of each feature, for distance scaling


def failure_modes(f):
    modes = []
    if f["kind"] == "produce":
        return [dict(mode="respiration", why="Living tissue keeps breathing: O₂ and CO₂ must be balanced")]
    aw = f.get("aw_in")
    if aw is not None and aw >= 0.85 and (f.get("ph") or 7) > 4.6:
        modes.append(dict(mode="microbial", why=f"aw {aw:.2f} with pH above 4.6 supports bacterial growth"))
    if f["kind"] == "dry":
        modes.append(dict(mode="moisture gain", why=f"Low water activity ({aw:.2f}) pulls water from humid air: sogginess or caking"))
    if (f.get("fat") or 0) >= 15 or f.get("o2") in ("high", "aroma"):
        modes.append(dict(mode="oxidation", why=f"Fat {f.get('fat', 0):g} %: rancidity from oxygen and light"))
    if f.get("light"):
        modes.append(dict(mode="light", why="Colour or fat degrades under light"))
    if f["kind"] == "frozen":
        modes.append(dict(mode="freezer burn", why="Ice sublimes through a leaky film at −18 °C"))
    return modes


class Estimator:
    def __init__(self, foods):
        self.ref = [f for f in foods if f["kind"] == "dry"]
        X = np.array([[f[k] for k in FEATURES] for f in self.ref]) / SCALE
        self.nn = NearestNeighbors(n_neighbors=min(3, len(self.ref))).fit(X)

    def estimate(self, comp):
        x = np.array([[comp[k] for k in FEATURES]]) / SCALE
        dist, idx = self.nn.kneighbors(x)
        dist, idx = dist[0], idx[0]
        w = 1 / (dist + 0.15)
        w = w / w.sum()
        refs = [self.ref[i] for i in idx]
        ratio = sum(wi * (r["mc"] / r["mi"]) for wi, r in zip(w, refs))
        aw = sum(wi * r["aw_in"] for wi, r in zip(w, refs))
        o2_vote = {}
        for wi, r in zip(w, refs):
            o2_vote[r["o2"]] = o2_vote.get(r["o2"], 0) + wi
        o2 = max(o2_vote, key=o2_vote.get)
        if comp["fat"] >= 15 and o2 == "low":
            o2 = "high"
        conf = float(np.clip(1 / (1 + dist.min()), 0, 1))
        light = sum(wi for wi, r in zip(w, refs) if r["light"]) > 0.5 or comp["fat"] >= 15
        return dict(
            mc=round(comp["mi"] * ratio, 2), aw_in=round(float(aw), 2), o2=o2, light=bool(light), confidence=round(conf, 2),
            level="good" if conf >= 0.7 else "fair" if conf >= 0.45 else "low",
            neighbours=[dict(id=r["id"], name=r["name"], similarity=round(float(1 / (1 + d)), 2), weight=round(float(wi), 2))
                        for r, d, wi in zip(refs, dist, w)],
        )
