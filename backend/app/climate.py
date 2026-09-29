"""Monthly climate per city from the Open-Meteo historical archive (last full year), cached in SQLite."""
import datetime as dt
import httpx
from . import db
from .data.seed import CITIES

FALLBACK = [dict(T=28.0, RH=0.72)] * 12


def monthly(city):
    data, source = db.climate_get(city)
    if data:
        return data, source
    lat, lon = CITIES[city]
    year = dt.date.today().year - 1
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = dict(latitude=lat, longitude=lon, start_date=f"{year}-01-01", end_date=f"{year}-12-31",
                  daily="temperature_2m_mean,relative_humidity_2m_mean", timezone="Asia/Kolkata")
    try:
        r = httpx.get(url, params=params, timeout=12)
        r.raise_for_status()
        d = r.json()["daily"]
        sums = [[0.0, 0.0, 0] for _ in range(12)]
        for day, t, h in zip(d["time"], d["temperature_2m_mean"], d["relative_humidity_2m_mean"]):
            if t is None or h is None:
                continue
            m = int(day[5:7]) - 1
            sums[m][0] += t; sums[m][1] += h; sums[m][2] += 1
        out = [dict(T=round(s[0] / s[2], 1), RH=round(s[1] / s[2] / 100, 3)) for s in sums]
        src = f"Open-Meteo archive {year}"
        db.climate_put(city, out, src)
        return out, src
    except Exception:
        return FALLBACK, "offline default (28 °C / 72 % RH) - connect to fetch real climate"
