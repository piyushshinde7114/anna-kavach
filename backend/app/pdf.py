"""Spec sheet PDF for the film converter, with a QR code that opens the trace page."""
import io
import os
import qrcode
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

FONT, BOLD = "Helvetica", "Helvetica-Bold"
for reg, bold in (("C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/arialbd.ttf"),
                  ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")):
    if os.path.exists(reg) and os.path.exists(bold):
        pdfmetrics.registerFont(TTFont("AK", reg)); pdfmetrics.registerFont(TTFont("AK-Bold", bold))
        FONT, BOLD = "AK", "AK-Bold"
        break

INK = (0.10, 0.16, 0.20)
LEAF = (0.10, 0.45, 0.35)
LAYER_COLS = {"PE": (0.72, 0.86, 0.78), "PP": (0.66, 0.76, 0.88), "PET": (0.80, 0.74, 0.90), "AL": (0.62, 0.64, 0.67),
              "PA": (0.93, 0.80, 0.62), "PLA": (0.88, 0.85, 0.60), "PAPER": (0.80, 0.66, 0.48), "PE+EVOH": (0.60, 0.82, 0.80)}


def _t(s):
    return (str(s).replace("₂", "2").replace("₹", "Rs ").replace("→", "->").replace("≤", "<=").replace("≥", ">=")
            .replace("−", "-").replace("·", "-"))


def spec_lines(p):
    r = p["result"]
    food = r["food"]
    L = []
    if "map" in r:
        m = r["map"]
        L.append(("Product", f"{food['name']}, {r['fill_kg']} kg per bag"))
        L.append(("Route", " -> ".join(f"{l['name']} {l['hours']:g} h @ {l['temp_c']:g} C" for l in r["legs"])))
        if m.get("design"):
            d = m["design"]
            L += [("Film", f"{m['film_name']}, bag area {d['area']:.2f} m2 (both faces)"),
                  ("Perforation", f"{d['holes']} laser micro-perforations, 100 um"),
                  ("Target headspace", f"O2 {food['o2_window'][0]}-{food['o2_window'][1]} %, CO2 {food['co2_window'][0]}-{food['co2_window'][1]} %"),
                  ("Handling", "Open the bag or pull the vent strip when it leaves the cold chain" if m.get("vent_at") is not None else "None"),
                  ("Temperature", f"Keep at or above {food['chill_c']} C; MAP valid only while at or below 15 C"),
                  ("Model result", f"{m['final']['window_h']:.0f} h in target window, {m['final']['injury_h']:.0f} h in injury zone")]
        else:
            L += [("Pack", "Macro-perforated bag or ventilated crate; protect the cold chain"),
                  ("Reason", "Sealed-film MAP cannot reach the target gas window on this route")]
    else:
        d = r["dry"]
        rec_ids = d["picks"].get("green")
        rec = next((c for c in d["candidates"] if c["ids"] == rec_ids), None)
        pk = r["pack"]
        L.append(("Product", f"{food['name']}, {pk['weight_g']:g} g, pouch {pk['width_cm']:g} x {pk['height_cm']:g} cm"))
        L.append(("Target", f"{r['target_days']} days, climate: {r['climate']['source']}"))
        if rec:
            L.append(("Structure", f"{rec['name']} ({rec['eco']['label']}, EPR {rec['eco']['epr']})"))
            if d["requirement"]["wvtr_max"]:
                L.append(("WVTR required", f"<= {d['requirement']['wvtr_max']:.2f} g/m2.day at 38 C / 90 % RH (ASTM F1249)"))
            L.append(("WVTR supplied", f"{rec['wvtr'][0]:.2f}-{rec['wvtr'][1]:.2f} g/m2.day"))
            L.append(("OTR supplied", f"{rec['otr'][0]:.2f}-{rec['otr'][1]:.1f} cc/m2.day.atm (23 C)"))
            if d["requirement"]["n2_flush"]:
                L.append(("Oxygen", "Nitrogen flush; keep residual O2 as low as practical"))
            if rec.get("life"):
                L.append(("Predicted shelf life", f"P10 {rec['life']['p10']:.0f} d, median {rec['life']['p50']:.0f} d, P90 {rec['life']['p90']:.0f} d (moisture, model)"))
            for n in rec.get("notes", []):
                L.append(("Note", n))
        else:
            L.append(("Result", "No composed structure passes. Shorten the target or reduce pouch size."))
    L.append(("Food contact", "Sealant must meet FSSAI Packaging Regulations 2018 and IS 9845 migration limits"))
    L.append(("Validation", "Confirm with an accelerated shelf-life test on 3 trial packs before scale-up"))
    return [(a, _t(b)) for a, b in L]


def render(p, public_url):
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    W, H = A4
    c.setFillColorRGB(*LEAF); c.rect(0, H - 34 * mm, W, 34 * mm, stroke=0, fill=1)
    c.setFillColorRGB(1, 1, 1); c.setFont(BOLD, 22); c.drawString(18 * mm, H - 18 * mm, "Anna Kavach")
    c.setFont(FONT, 10); c.drawString(18 * mm, H - 25 * mm, "Packaging specification for the film converter")
    c.drawRightString(W - 18 * mm, H - 18 * mm, p["trace_code"])
    c.setFillColorRGB(*INK); c.setFont(BOLD, 15)
    c.drawString(18 * mm, H - 46 * mm, _t(p["title"])[:80])
    y = H - 56 * mm
    # layer drawing
    r = p["result"]
    layers = []
    if "dry" in r:
        ids = r["dry"]["picks"].get("green")
        rec = next((x for x in r["dry"]["candidates"] if x["ids"] == ids), None)
        layers = rec["layers"] if rec else []
    if layers:
        c.setFont(FONT, 8)
        for i, l in enumerate(layers):
            c.setFillColorRGB(*LAYER_COLS.get(l["family"], (0.8, 0.8, 0.8)))
            c.rect(18 * mm, y - i * 7 * mm, 50 * mm, 5.5 * mm, stroke=0, fill=1)
            c.setFillColorRGB(*INK); c.drawString(71 * mm, y - i * 7 * mm + 1.6 * mm, _t(l["name"]))
        y -= len(layers) * 7 * mm + 4 * mm
    for k, v in spec_lines(p):
        c.setFont(BOLD, 9.5); c.drawString(18 * mm, y, k)
        c.setFont(FONT, 9.5)
        words, line = v.split(" "), ""
        for w in words:
            if c.stringWidth(line + " " + w, FONT, 9.5) > 120 * mm:
                c.drawString(62 * mm, y, line.strip()); y -= 4.8 * mm; line = ""
            line += " " + w
        c.drawString(62 * mm, y, line.strip()); y -= 7 * mm
    img = qrcode.make(f"{public_url}/t/{p['trace_code']}", box_size=6, border=1)
    b = io.BytesIO(); img.save(b, format="PNG"); b.seek(0)
    c.drawImage(ImageReader(b), W - 58 * mm, 22 * mm, 40 * mm, 40 * mm)
    c.setFont(FONT, 8); c.drawRightString(W - 18 * mm, 18 * mm, f"Scan to verify: {public_url}/t/{p['trace_code']}")
    c.setFont(FONT, 7.5); c.setFillColorRGB(0.35, 0.4, 0.42)
    c.drawString(18 * mm, 18 * mm, "Model output. Film values are indicative ranges; supplier datasheets override them.")
    c.drawString(18 * mm, 14 * mm, "Anna Kavach advises; it does not certify food safety.")
    c.showPage(); c.save()
    return buf.getvalue()
