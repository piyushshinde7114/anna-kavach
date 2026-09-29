"""Anna Kavach API (FastAPI)."""
import os
from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import Optional, List

from . import db, service, pdf, climate
from .data.seed import CITIES, CITY_HI, SOURCES, O2_RULES
from .engine import intake
from .engine.profiler import Estimator, failure_modes

ADMIN_TOKEN = os.environ.get("ANNAKAVACH_ADMIN_TOKEN", "annakavach-admin")
PUBLIC_URL = os.environ.get("ANNAKAVACH_PUBLIC_URL", "http://localhost:8000")

app = FastAPI(title="Anna Kavach API", version="0.9.0",
              description="Physics-first packaging recommendation for Indian food commodities (SIH26236).")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
db.init()


class Comp(BaseModel):
    name: str = "Custom food"
    mi: float = Field(ge=0.1, le=40)
    fat: float = Field(ge=0, le=100)
    protein: float = Field(ge=0, le=100)
    carb: float = Field(ge=0, le=100)


class Pack(BaseModel):
    weight_g: float = Field(gt=5, le=50000)
    width_cm: float = Field(gt=3, le=120)
    height_cm: float = Field(gt=3, le=160)


class Leg(BaseModel):
    name: str
    hours: float = Field(gt=0, le=2000)
    temp_c: float = Field(ge=-30, le=50)


class Route(BaseModel):
    origin: Optional[str] = None
    destination: Optional[str] = None
    month: int = Field(0, ge=0, le=11)
    mode: str = "reefer"
    transit_c: Optional[float] = None
    retail_hours: float = 48
    cold_store_hours: float = 0


class RecommendIn(BaseModel):
    food_id: Optional[str] = None
    custom: Optional[Comp] = None
    pack: Optional[Pack] = None
    fill_kg: Optional[float] = Field(None, gt=0.1, le=25)
    target_days: Optional[int] = Field(None, ge=3, le=1000)
    route: Optional[Route] = None
    legs: Optional[List[Leg]] = None
    storage: Optional[str] = None


def _admin(tok):
    if tok != ADMIN_TOKEN:
        raise HTTPException(401, "Admin token required")


@app.get("/api/meta")
def meta():
    fs = db.foods()
    return dict(
        foods=[dict(id=f["id"], name=f["name"], hi=f.get("hi"), kind=f["kind"], category=f["category"],
                    pack=f.get("pack"), target_days=f.get("target_days"), fill_kg=f.get("fill_kg"), store_c=f.get("store_c"))
               for f in fs],
        cities=[dict(name=c, hi=CITY_HI.get(c), lat=v[0], lon=v[1]) for c, v in CITIES.items()],
        counts=dict(foods=len(fs), films=len(db.films()), projects=len(db.list_projects(1000)), reports=len(db.feedback())),
        sources=SOURCES)


@app.get("/api/foods")
def foods():
    return [dict(f, failure_modes=failure_modes(f)) for f in db.foods()]


@app.get("/api/films")
def films():
    return list(db.films().values())


@app.put("/api/films/{fid}")
def update_film(fid: str, body: dict, x_admin_token: str = Header(None)):
    _admin(x_admin_token)
    fs = db.films()
    if fid not in fs:
        raise HTTPException(404, "Unknown film")
    f = fs[fid]
    for k in ("otr", "wvtr", "cost_m2"):
        if k in body:
            lo, hi = float(body[k][0]), float(body[k][1])
            if not (0 < lo <= hi):
                raise HTTPException(422, f"{k}: low must be positive and not above high")
            f[k] = [lo, hi]
    if "co2e" in body:
        f["co2e"] = float(body["co2e"])
    f["conf"] = dict(f.get("conf", {}), edited="admin")
    db.put("films", fid, f)
    return f


@app.post("/api/admin/check")
def admin_check(x_admin_token: str = Header(None)):
    _admin(x_admin_token)
    return dict(ok=True)


@app.post("/api/foods/estimate")
def estimate(c: Comp):
    return Estimator(db.foods()).estimate(c.model_dump())


@app.post("/api/intake")
def parse_intake(body: dict):
    return intake.parse(body.get("text", ""), db.foods(), list(CITIES), CITY_HI)


@app.get("/api/climate/{city}")
def get_climate(city: str):
    if city not in CITIES:
        raise HTTPException(404, "Unknown city")
    data, src = climate.monthly(city)
    return dict(city=city, source=src, months=data)


@app.post("/api/recommend")
def recommend(body: RecommendIn):
    try:
        return service.recommend(body.model_dump(exclude_none=True))
    except service.InputError as e:
        raise HTTPException(422, str(e))


@app.get("/api/projects")
def projects():
    return db.list_projects()


@app.get("/api/projects/{pid}")
def project(pid: str):
    p = db.get_project(pid=pid)
    if not p:
        raise HTTPException(404, "Project not found")
    p["result"]["project_id"], p["result"]["trace_code"] = p["id"], p["trace_code"]
    return p


@app.delete("/api/projects/{pid}")
def delete_project(pid: str):
    db.delete_project(pid)
    return dict(ok=True)


@app.post("/api/projects/{pid}/simulate")
def simulate(pid: str, legs: List[Leg]):
    try:
        return service.resimulate(pid, [l.model_dump() for l in legs])
    except service.InputError as e:
        raise HTTPException(422, str(e))


@app.get("/api/projects/{pid}/pdf")
def spec_pdf(pid: str, request: Request):
    p = db.get_project(pid=pid)
    if not p:
        raise HTTPException(404, "Project not found")
    base = os.environ.get("ANNAKAVACH_PUBLIC_URL") or str(request.base_url).rstrip("/")
    return Response(pdf.render(p, base), media_type="application/pdf",
                    headers={"Content-Disposition": f'inline; filename="AnnaKavach_{p["trace_code"]}.pdf"'})


@app.get("/api/qr/{code}.svg")
def qr_svg(code: str, request: Request):
    import io
    import qrcode
    import qrcode.image.svg
    base = os.environ.get("ANNAKAVACH_PUBLIC_URL") or str(request.base_url).rstrip("/")
    img = qrcode.make(f"{base}/t/{code}", image_factory=qrcode.image.svg.SvgPathImage, box_size=8, border=1)
    b = io.BytesIO(); img.save(b)
    return Response(b.getvalue(), media_type="image/svg+xml")


@app.get("/api/trace/{code}")
def trace(code: str):
    p = db.get_project(code=code)
    if not p:
        raise HTTPException(404, "No pack is registered with this code")
    return dict(code=code, title=p["title"], created=p["created"], kind=p["kind"], food=p["result"]["food"]["name"],
                spec=pdf.spec_lines(p), batches=db.batches(p["id"]), feedback=db.feedback(pid=p["id"]),
                calibration=db.calibration(p["food_id"]), project_id=p["id"])


class BatchIn(BaseModel):
    lot: str = Field(min_length=1, max_length=40)
    packed_on: str
    quantity: int = Field(ge=1, le=10_000_000)


@app.post("/api/trace/{code}/batches")
def add_batch(code: str, b: BatchIn):
    p = db.get_project(code=code)
    if not p:
        raise HTTPException(404, "Unknown code")
    db.add_batch(p["id"], b.lot, b.packed_on, b.quantity)
    return db.batches(p["id"])


class FeedbackIn(BaseModel):
    observed_days: float = Field(gt=0, le=2000)
    outcome: str = Field(pattern="^(fine|soggy|rancid|mould|fermented|bruised|other)$")
    notes: str = Field("", max_length=500)


@app.post("/api/trace/{code}/feedback")
def add_feedback(code: str, fb: FeedbackIn):
    p = db.get_project(code=code)
    if not p:
        raise HTTPException(404, "Unknown code")
    r = p["result"]
    predicted, structure = None, None
    if "dry" in r and r["dry"]["picks"].get("green"):
        ids = r["dry"]["picks"]["green"]
        rec = next(c for c in r["dry"]["candidates"] if c["ids"] == ids)
        structure = rec["name"]
        predicted = rec["life"]["p50"] if rec.get("life") else None
    db.add_feedback(p["id"], p["food_id"], structure, predicted, fb.observed_days, fb.outcome, fb.notes)
    return dict(ok=True, calibration=db.calibration(p["food_id"]))


@app.get("/api/calibration")
def calibration():
    return {f["id"]: db.calibration(f["id"]) for f in db.foods()}


# ---- serve the built web app (single command demo)
DIST = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist")
if os.path.isdir(DIST):
    app.mount("/assets", StaticFiles(directory=os.path.join(DIST, "assets")), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str):
        fp = os.path.join(DIST, path)
        if path and os.path.isfile(fp):
            return FileResponse(fp)
        return FileResponse(os.path.join(DIST, "index.html"))
