"""Core physical relations. Units are stated on every function."""
import math

R_GAS = 8.314  # J/(mol.K)
O2_MG_PER_ML = 1.43  # mg O2 per mL at ~0 C, 1 atm
TEST_T, TEST_RH = 38.0, 0.90  # ASTM F1249 / E96 tropical test condition for WVTR


def psat_kpa(t_c: float) -> float:
    """Saturation vapour pressure of water, kPa (Magnus-Tetens)."""
    return 0.61078 * math.exp(17.27 * t_c / (t_c + 237.3))


def dp_kpa(t_c: float, rh: float, aw_in: float) -> float:
    """Water-vapour partial-pressure difference across the pack wall, kPa (0 if the room is drier than the food)."""
    return max(0.0, psat_kpa(t_c) * (rh - aw_in))


DP_TEST = psat_kpa(TEST_T) * TEST_RH


def arrhenius(value: float, ea_j: float, t_c: float, tref_c: float) -> float:
    """Scale a rate from tref_c to t_c with activation energy ea_j (J/mol)."""
    return value * math.exp(ea_j / R_GAS * (1 / (tref_c + 273.15) - 1 / (t_c + 273.15)))


def series(values):
    """Layers in series: 1/P_total = sum(1/P_i). Works for WVTR, OTR or permeance of one layer each."""
    return 1.0 / sum(1.0 / v for v in values)


def haversine_km(a, b) -> float:
    (la1, lo1), (la2, lo2) = a, b
    p1, p2 = math.radians(la1), math.radians(la2)
    dl, dp = math.radians(lo2 - lo1), p2 - p1
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * 6371 * math.asin(math.sqrt(h))
