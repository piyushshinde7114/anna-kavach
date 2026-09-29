"""Seed knowledge base for Anna Kavach.

Every value carries a `conf` level:
  "sourced"  - taken from a cited public source (see SOURCES)
  "typical"  - rounded literature / datasheet range, to be checked against supplier data
  "demo"     - placeholder for the MVP (cost bands), to be replaced with converter quotes
Admins can edit films and foods through the API; the DB copy is the working copy.
"""

SOURCES = {
    "ucd_mango": {"title": "UC Davis Postharvest Center - Mango produce facts", "url": "https://postharvest.ucdavis.edu/produce-facts-sheets/mango"},
    "ucd_tomato": {"title": "UC Davis Postharvest Center - Tomato produce facts", "url": "https://postharvest.ucdavis.edu/produce-facts-sheets/tomato"},
    "usda_hb66": {"title": "USDA Agriculture Handbook 66 - Commercial Storage of Fruits, Vegetables", "url": "https://www.ars.usda.gov/is/np/CommercialStorage/CommercialStorage.pdf"},
    "kader": {"title": "Kader A.A. - summary of CA/MA requirements for fresh produce (UC Davis)", "url": "https://postharvest.ucdavis.edu/"},
    "ifct": {"title": "Indian Food Composition Tables 2017, ICMR-NIN", "url": "https://www.nin.res.in/ebooks/IFCT2017.pdf"},
    "ift_moisture": {"title": "IFT - Controlling moisture in foods using packaging", "url": "https://www.ift.org/food-technology-magazine/packaging-controlling-moisture"},
    "robertson": {"title": "Robertson G.L. - Food Packaging and Shelf Life: A Practical Guide (CRC)", "url": "https://www.routledge.com/Food-Packaging-and-Shelf-Life-A-Practical-Guide/Robertson/p/book/9781420078442"},
    "fssai_pack": {"title": "FSSAI Packaging Regulations 2018 (compendium)", "url": "https://fssai.gov.in/upload/uploadfiles/files/Compendium_Packaging_01_02_2022.pdf"},
    "pwm_2022": {"title": "Plastic Waste Management (Amendment) Rules 2022 - EPR categories", "url": "https://leap.unep.org/en/countries/in/national-legislation/plastic-waste-management-amendment-rules-2022-0"},
    "cpcb_comp": {"title": "CPCB SOP - compostable plastics certification (IS/ISO 17088)", "url": "https://cpcb.gov.in/uploads/plasticwaste/SOP-IssueCert-CompostablePlasticManufacturers.pdf"},
    "arcc_alphonso": {"title": "Respiration behaviour of Alphonso mango (Asian J. Dairy & Food Res.)", "url": "https://arccjournals.com/journal/asian-journal-of-dairy-and-food-research/DR-1843"},
    "openmeteo": {"title": "Open-Meteo historical weather API", "url": "https://open-meteo.com/en/docs/historical-weather-api"},
}

# ---------------------------------------------------------------- films
# otr: cc/(m2.day.atm) at 23 C, 0 % RH   wvtr: g/(m2.day) at 38 C / 90 % RH
# cost_m2: INR per m2 (demo band)   co2e: kg CO2e per kg material (indicative cradle-to-gate)
FILMS = [
    dict(id="LDPE25", name="LDPE 25 µm", family="PE", um=25, density=0.92, otr=[7000, 8000], wvtr=[15, 20], beta=4.5,
         seal=True, tmin=-50, tmax=80, grease="good", opaque=False, cost_m2=[3, 4], co2e=1.9, roles=["sealant", "map"]),
    dict(id="LDPE50", name="LDPE 50 µm", family="PE", um=50, density=0.92, otr=[3500, 4000], wvtr=[7, 9], beta=4.5,
         seal=True, tmin=-50, tmax=80, grease="good", opaque=False, cost_m2=[6, 8], co2e=1.9, roles=["sealant", "map", "mono"]),
    dict(id="LLDPE50", name="LLDPE 50 µm", family="PE", um=50, density=0.92, otr=[3500, 4500], wvtr=[7, 10], beta=4.5,
         seal=True, tmin=-60, tmax=90, grease="good", opaque=False, cost_m2=[7, 9], co2e=1.9, roles=["sealant"]),
    dict(id="HDPE25", name="HDPE 25 µm", family="PE", um=25, density=0.95, otr=[2000, 3000], wvtr=[5, 8], beta=4.0,
         seal=True, tmin=-50, tmax=110, grease="good", opaque=False, cost_m2=[3, 4], co2e=1.8, roles=["mono"]),
    dict(id="CPP30", name="CPP 30 µm", family="PP", um=30, density=0.90, otr=[1500, 3000], wvtr=[8, 12], beta=3.5,
         seal=True, tmin=0, tmax=120, grease="good", opaque=False, cost_m2=[6, 8], co2e=1.7, roles=["sealant", "map"]),
    dict(id="BOPP20", name="BOPP 20 µm", family="PP", um=20, density=0.905, otr=[1500, 2500], wvtr=[5, 7], beta=3.5,
         seal=False, tmin=-40, tmax=120, grease="good", opaque=False, cost_m2=[4, 5], co2e=1.7, roles=["outer", "map"]),
    dict(id="mBOPP20", name="met-BOPP 20 µm", family="PP", um=20, density=0.905, otr=[20, 150], wvtr=[0.2, 1.0], beta=3.5,
         seal=True, tmin=-40, tmax=120, grease="good", opaque=True, cost_m2=[6, 8], co2e=1.8, roles=["barrier", "sealant"]),
    dict(id="PET12", name="PET 12 µm", family="PET", um=12, density=1.39, otr=[100, 120], wvtr=[40, 55], beta=4.0,
         seal=False, tmin=-60, tmax=150, grease="good", opaque=False, cost_m2=[5, 6], co2e=2.7, roles=["outer"]),
    dict(id="mPET12", name="met-PET 12 µm", family="PET", um=12, density=1.39, otr=[0.5, 2], wvtr=[0.5, 1.5], beta=4.0,
         seal=False, tmin=-60, tmax=150, grease="good", opaque=True, cost_m2=[7, 9], co2e=2.8, roles=["barrier", "outer"]),
    dict(id="AlOxPET12", name="AlOx-PET 12 µm (clear)", family="PET", um=12, density=1.39, otr=[0.5, 3], wvtr=[0.5, 2], beta=4.0,
         seal=False, tmin=-60, tmax=150, grease="good", opaque=False, cost_m2=[18, 25], co2e=2.9, roles=["outer"]),
    dict(id="BOPA15", name="BOPA (nylon) 15 µm", family="PA", um=15, density=1.14, otr=[20, 40], wvtr=[150, 300], beta=4.0,
         seal=False, tmin=-60, tmax=150, grease="good", opaque=False, cost_m2=[12, 15], co2e=8.0, roles=["outer"]),
    dict(id="EVOHPE60", name="PE/EVOH/PE coex 60 µm", family="PE+EVOH", um=60, density=0.95, otr=[1, 5], wvtr=[5, 8], beta=4.0,
         seal=True, tmin=-50, tmax=90, grease="good", opaque=False, cost_m2=[15, 20], co2e=2.2, roles=["sealant"]),
    dict(id="AL9", name="Al foil 9 µm", family="AL", um=9, density=2.70, otr=[0.01, 0.5], wvtr=[0.01, 0.1], beta=1.0,
         seal=False, tmin=-80, tmax=300, grease="good", opaque=True, cost_m2=[15, 20], co2e=9.0, roles=["barrier"]),
    dict(id="PLA25", name="PLA 25 µm (compostable)", family="PLA", um=25, density=1.24, otr=[500, 900], wvtr=[150, 300], beta=4.0,
         seal=True, tmin=-20, tmax=55, grease="poor", opaque=False, cost_m2=[15, 22], co2e=1.3, roles=["mono"]),
    dict(id="KRAFT60", name="Kraft paper 60 gsm", family="PAPER", um=80, density=0.75, otr=[1e6, 1e6], wvtr=[500, 900], beta=1.0,
         seal=False, tmin=-40, tmax=150, grease="poor", opaque=True, cost_m2=[5, 7], co2e=1.0, roles=["outer"]),
]
for f in FILMS:
    f["conf"] = {"barrier": "typical", "cost": "demo", "co2e": "typical"}
    f["source"] = "robertson"
LAMINATION_COST_M2 = [2, 3]  # INR per bond line (demo)

# ---------------------------------------------------------------- foods
# Dry foods: mi, mc = initial / critical moisture, % dry basis; aw_in = water activity inside the pack.
# o2: sensitivity class used by the oxygen rule (admin-configurable); light: light-sensitive.
def dry(id, name, cat, mi, mc, aw, fat, prot, carb, o2, light, wt, days, w, h, hi=None, **kw):
    d = dict(id=id, name=name, hi=hi or name, kind="dry", category=cat, mi=mi, mc=mc, aw_in=aw, fat=fat, protein=prot,
             carb=carb, ph=6.0, o2=o2, light=light, pack=dict(weight_g=wt, width_cm=w, height_cm=h), target_days=days,
             conf=dict(mi="typical", mc="assumed", fat="typical", aw_in="assumed"), source="ifct")
    d.update(kw)
    return d

FOODS = [
    dry("banana_chips", "Banana chips (fried)", "Snacks", 2.5, 5.0, 0.30, 35, 2, 58, "high", True, 200, 180, 15, 22, hi="केला चिप्स", aliases=["kela chips", "banana chips", "nendran chips"]),
    dry("potato_chips", "Potato chips (fried)", "Snacks", 2.0, 4.5, 0.30, 35, 6, 52, "high", True, 100, 120, 14, 20, hi="आलू चिप्स", aliases=["aloo chips", "potato wafers"]),
    dry("namkeen", "Namkeen / bhujia", "Snacks", 3.0, 6.0, 0.35, 35, 12, 45, "high", True, 400, 150, 18, 26, hi="नमकीन / भुजिया", aliases=["bhujia", "mixture", "farsan"]),
    dry("peanuts_roasted", "Roasted peanuts", "Nuts", 2.0, 5.0, 0.30, 48, 26, 16, "high", True, 500, 180, 18, 28, hi="भुनी मूंगफली", aliases=["mungfali", "groundnut", "peanut"]),
    dry("cashew", "Cashew kernels", "Nuts", 4.0, 7.0, 0.40, 44, 18, 30, "high", True, 250, 270, 16, 24, hi="काजू", aliases=["kaju"]),
    dry("makhana", "Makhana (roasted)", "Snacks", 4.0, 8.0, 0.35, 0.5, 9, 77, "low", False, 100, 180, 20, 28, hi="मखाना", aliases=["fox nut", "lotus seed"]),
    dry("biscuits", "Biscuits / cookies", "Bakery", 3.0, 6.0, 0.30, 18, 7, 70, "medium", False, 200, 180, 12, 22, hi="बिस्किट", aliases=["cookies"]),
    dry("rusk", "Rusk / toast", "Bakery", 4.0, 7.0, 0.35, 10, 10, 72, "medium", False, 300, 180, 16, 28, hi="रस्क", aliases=["toast"]),
    dry("instant_noodles", "Instant noodles (fried)", "Ready to cook", 5.0, 8.0, 0.40, 18, 9, 60, "high", False, 70, 270, 14, 18, hi="इंस्टेंट नूडल्स", aliases=["noodles", "maggi"]),
    dry("turmeric", "Turmeric powder", "Spices", 8.0, 12.0, 0.45, 5, 8, 65, "low", True, 200, 365, 14, 20, hi="हल्दी पाउडर", aliases=["haldi"]),
    dry("chilli_powder", "Red chilli powder", "Spices", 8.0, 12.0, 0.45, 12, 12, 50, "medium", True, 200, 365, 14, 20, hi="लाल मिर्च पाउडर", aliases=["mirchi", "lal mirch"]),
    dry("jaggery", "Jaggery cubes", "Sweeteners", 5.0, 8.0, 0.50, 0.1, 0.5, 90, "low", False, 1000, 180, 22, 32, hi="गुड़", aliases=["gud", "gur"]),
    dry("milk_powder", "Whole milk powder", "Dairy", 3.0, 5.0, 0.25, 26, 26, 38, "high", True, 500, 365, 18, 28, hi="दूध पाउडर", aliases=["dudh powder"]),
    dry("atta", "Whole wheat flour (atta)", "Staples", 12.0, 15.0, 0.60, 2, 12, 70, "medium", False, 5000, 120, 30, 45, hi="आटा", aliases=["atta", "wheat flour"]),
    dry("tea_ctc", "Tea (CTC)", "Beverages", 5.0, 8.0, 0.40, 2, 20, 50, "aroma", True, 250, 365, 14, 22, hi="चाय पत्ती", aliases=["chai", "tea"]),
    dry("coffee_ground", "Roasted ground coffee", "Beverages", 3.0, 6.0, 0.30, 12, 14, 40, "high", True, 250, 270, 14, 22, hi="कॉफी", aliases=["coffee"],
        degas=True),
    dict(id="ghee", name="Ghee", hi="घी", kind="fat", category="Dairy", mi=None, mc=None, aw_in=None, fat=99.5, protein=0, carb=0,
         ph=None, o2="high", light=True, pack=dict(weight_g=500, width_cm=16, height_cm=22), target_days=270,
         conf=dict(fat="typical"), source="robertson", aliases=["ghee", "clarified butter"]),
    dict(id="paneer", name="Paneer (chilled)", hi="पनीर", kind="chilled", category="Dairy", mi=None, mc=None, aw_in=0.97, fat=22,
         protein=18, carb=3, ph=5.8, o2="microbial", light=False, pack=dict(weight_g=200, width_cm=15, height_cm=20), target_days=15,
         store_c=4, conf=dict(aw_in="typical"), source="robertson", aliases=["paneer", "cottage cheese"]),
    dict(id="green_peas_frozen", name="Green peas (frozen)", hi="फ्रोजन मटर", kind="frozen", category="Frozen", mi=None, mc=None,
         aw_in=0.99, fat=0.4, protein=5, carb=14, ph=6.5, o2="low", light=False, pack=dict(weight_g=500, width_cm=18, height_cm=28),
         target_days=365, store_c=-18, conf=dict(), source="robertson", aliases=["matar", "frozen peas"]),
]

# Fresh produce: respiration R13 = mL O2 / kg.h at 13 C, Q10, Km (O2 fraction); windows in % gas.
def fresh(id, name, R13, Q10, o2, co2, o2min, co2max, chill, conf, src, hi, aliases, store_c):
    return dict(id=id, name=name, hi=hi, kind="produce", category="Fresh produce", R13=R13, Q10=Q10, Km=0.015, RQ=1.0,
                o2_window=o2, co2_window=co2, o2_min=o2min, co2_max=co2max, chill_c=chill, store_c=store_c, fill_kg=1.0,
                free_l_per_kg=0.8, conf=conf, source=src, aliases=aliases)

FOODS += [
    fresh("mango", "Mango, Alphonso (fresh)", 18, 2.2, [3, 5], [5, 8], 2, 8, 12,
          dict(window="sourced", respiration="assumed"), "ucd_mango", "आम (हापुस)", ["aam", "hapus", "alphonso", "mango"], 13),
    fresh("tomato", "Tomato, mature green (fresh)", 8, 2.2, [3, 5], [0, 3], 2, 5, 10,
          dict(window="sourced", respiration="assumed"), "ucd_tomato", "टमाटर", ["tamatar", "tomato"], 12),
    fresh("banana", "Banana, green mature (fresh)", 12, 2.3, [2, 5], [2, 5], 1, 7, 13,
          dict(window="typical", respiration="assumed"), "kader", "केला", ["kela", "banana"], 14),
    fresh("capsicum", "Capsicum, green (fresh)", 8, 2.2, [3, 5], [0, 5], 2, 7, 7,
          dict(window="typical", respiration="assumed"), "kader", "शिमला मिर्च", ["shimla mirch", "bell pepper", "capsicum"], 8),
    fresh("pomegranate", "Pomegranate (fresh)", 4, 2.2, [3, 5], [5, 10], 2, 12, 5,
          dict(window="typical", respiration="assumed"), "kader", "अनार", ["anar", "pomegranate"], 6),
    fresh("broccoli", "Broccoli (fresh)", 60, 2.5, [1, 2], [5, 10], 0.5, 15, -1,
          dict(window="typical", respiration="assumed"), "kader", "ब्रोकोली", ["broccoli"], 1),
]

# ---------------------------------------------------------------- oxygen rules (heuristic, admin-configurable)
O2_RULES = {
    "high": {"otr_max": 150, "n2_flush": True, "note": "Fatty or oxidation-prone: metallised or foil barrier + nitrogen flush"},
    "aroma": {"otr_max": 20, "n2_flush": False, "note": "Aroma loss: very high barrier to O2 and volatiles"},
    "medium": {"otr_max": 500, "n2_flush": False, "note": "Moderate oxidation risk"},
    "low": {"otr_max": None, "n2_flush": False, "note": "Oxygen not limiting"},
    "microbial": {"otr_max": 50, "n2_flush": False, "note": "High water activity: vacuum or MAP pack, strict cold chain"},
}

# ---------------------------------------------------------------- cities (lat, lon)
CITIES = {
    "Ratnagiri": (16.99, 73.30), "Mumbai": (19.08, 72.88), "Pune": (18.52, 73.86), "Nashik": (20.00, 73.79),
    "Nagpur": (21.15, 79.09), "Delhi": (28.61, 77.21), "Kolkata": (22.57, 88.36), "Chennai": (13.08, 80.27),
    "Bengaluru": (12.97, 77.59), "Hyderabad": (17.39, 78.49), "Ahmedabad": (23.02, 72.57), "Jaipur": (26.91, 75.79),
    "Lucknow": (26.85, 80.95), "Patna": (25.59, 85.14), "Guwahati": (26.14, 91.74), "Kochi": (9.93, 76.27),
    "Thiruvananthapuram": (8.52, 76.94), "Coimbatore": (11.02, 76.96), "Indore": (22.72, 75.86), "Bhopal": (23.26, 77.41),
    "Chandigarh": (30.73, 76.78), "Amritsar": (31.63, 74.87), "Srinagar": (34.08, 74.80), "Bhubaneswar": (20.30, 85.82),
    "Visakhapatnam": (17.69, 83.22), "Varanasi": (25.32, 82.97), "Kozhikode": (11.26, 75.78), "Surat": (21.17, 72.83),
}
CITY_HI = {"Ratnagiri": "रत्नागिरी", "Mumbai": "मुंबई", "Pune": "पुणे", "Nashik": "नासिक", "Nagpur": "नागपुर", "Delhi": "दिल्ली",
           "Kolkata": "कोलकाता", "Chennai": "चेन्नई", "Bengaluru": "बेंगलुरु", "Hyderabad": "हैदराबाद", "Jaipur": "जयपुर",
           "Lucknow": "लखनऊ", "Patna": "पटना", "Kochi": "कोच्चि", "Indore": "इंदौर", "Bhopal": "भोपाल", "Surat": "सूरत",
           "Ahmedabad": "अहमदाबाद", "Chandigarh": "चंडीगढ़", "Guwahati": "गुवाहाटी", "Varanasi": "वाराणसी"}
