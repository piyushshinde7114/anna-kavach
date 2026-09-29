"""Quick-ask parser: English, Hinglish or Hindi sentence -> structured request. Deterministic, no LLM.

Example: "200 g banana chips 6 months Kochi to Delhi"  /  "1 किलो आम रत्नागिरी से दिल्ली मई में"
"""
import re
import unicodedata

MONTHS = {"jan": 0, "feb": 1, "mar": 2, "apr": 3, "may": 4, "jun": 5, "jul": 6, "aug": 7, "sep": 8, "oct": 9, "nov": 10, "dec": 11,
          "जनवरी": 0, "फरवरी": 1, "मार्च": 2, "अप्रैल": 3, "मई": 4, "जून": 5, "जुलाई": 6, "अगस्त": 7, "सितंबर": 8, "अक्टूबर": 9,
          "नवंबर": 10, "दिसंबर": 11}
DEV_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")


def _norm(s):
    return unicodedata.normalize("NFC", s).translate(DEV_DIGITS).lower()


def parse(text, foods, cities, city_hi):
    t = _norm(text)
    out, found = {}, []
    # weight
    m = re.search(r"(\d+(?:\.\d+)?)\s*(kg|kilo|किलो|किग्रा)", t)
    if m:
        out["weight_g"] = float(m.group(1)) * 1000; found.append(m.group(0))
    else:
        m = re.search(r"(\d+(?:\.\d+)?)\s*(g|gm|gms|gram|grams|ग्राम)\b", t)
        if m:
            out["weight_g"] = float(m.group(1)); found.append(m.group(0))
    # duration
    m = re.search(r"(\d+(?:\.\d+)?)\s*(month|months|mahine|mahina|महीने|महीना|माह)", t)
    if m:
        out["target_days"] = round(float(m.group(1)) * 30.4); found.append(m.group(0))
    else:
        m = re.search(r"(\d+(?:\.\d+)?)\s*(year|years|saal|साल)", t)
        if m:
            out["target_days"] = round(float(m.group(1)) * 365); found.append(m.group(0))
        else:
            m = re.search(r"(\d+)\s*(day|days|din|दिन)", t)
            if m:
                out["target_days"] = int(m.group(1)); found.append(m.group(0))
    # food: longest alias match
    best = None
    for f in foods:
        hi = [p.strip() for p in f.get("hi", "").replace(")", "").split(" (") + f.get("hi", "").split("/")]
        names = [f["name"].lower().split(" (")[0].split(",")[0]] + hi + [a.lower() for a in f.get("aliases", [])]
        for n in names:
            n = n.strip()
            if n and n in t and (best is None or len(n) > best[1]):
                best = (f["id"], len(n), n)
    if best:
        out["food_id"] = best[0]; found.append(best[2])
    # cities in order of appearance
    hits = []
    for c in cities:
        for n in (c.lower(), city_hi.get(c, "#").lower()):
            i = t.find(n)
            if n != "#" and i >= 0:
                hits.append((i, c)); break
    hits.sort()
    if hits:
        out["origin"] = hits[0][1]
        if len(hits) > 1:
            out["destination"] = hits[1][1]
    for k, v in MONTHS.items():
        if re.search(rf"\b{k}", t) if k.isascii() else k in t:
            out["month"] = v; break
    if any(w in t for w in ("ambient", "without cold", "bina cold", "normal truck")):
        out["mode"] = "truck"
    elif any(w in t for w in ("reefer", "cold chain", "cold truck", "ठंडा", "कोल्ड")):
        out["mode"] = "reefer"
    missing = [k for k in ("food_id",) if k not in out]
    return dict(parsed=out, matched=found, missing=missing)
