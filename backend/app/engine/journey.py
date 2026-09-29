"""Route builder: turns origin, destination, month and transport mode into timed legs with temperatures."""
from .physics import haversine_km

SPEED = {"reefer": 45.0, "truck": 40.0, "rail": 35.0}
ROAD_FACTOR = 1.3


def build_legs(route, cities, clim_origin, clim_dest, food):
    m = route["month"]
    o, d = route["origin"], route["destination"]
    km = haversine_km(cities[o], cities[d]) * ROAD_FACTOR
    mode = route.get("mode", "reefer")
    hours = max(2.0, round(km / SPEED.get(mode, 40.0), 1))
    To, Td = clim_origin[m]["T"], clim_dest[m]["T"]
    if mode == "reefer":
        Tt = route.get("transit_c", food.get("store_c", 13))
        transit_name = f"Reefer truck {o} → {d}"
    else:
        Tt = round((To + Td) / 2 + 2, 1)  # closed truck body runs warmer than ambient
        transit_name = f"{'Rail' if mode == 'rail' else 'Truck'} {o} → {d} (ambient)"
    legs = [dict(name=f"Packhouse, {o}", hours=route.get("pack_hours", 2), temp_c=round(To, 1))]
    legs.append(dict(name=transit_name, hours=hours, temp_c=Tt))
    if route.get("cold_store_hours"):
        legs.append(dict(name=f"Cold store, {d}", hours=route["cold_store_hours"], temp_c=food.get("store_c", 13)))
    legs.append(dict(name=f"Retail, {d}", hours=route.get("retail_hours", 48), temp_c=round(Td, 1)))
    return dict(legs=legs, distance_km=round(km), transit_h=hours)
