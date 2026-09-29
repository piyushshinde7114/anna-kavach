# Anna Kavach (अन्न कवच) — SIH26236

Physics-first packaging recommendation system for Indian food commodities (MoFPI problem statement SIH26236).
You enter the food and its journey. The system works out how much protection the food needs on that route, then designs and ranks packs that deliver it, with the maths shown.

## Run it

```
start.bat
```
or, step by step:
```
cd backend
py -m pip install -r requirements.txt
cd ../frontend
npm install
npm run build
cd ..
py -m uvicorn app.main:app --port 8000 --app-dir backend
```
Open http://localhost:8000. API docs: http://localhost:8000/docs.
For front-end development run `npm run dev` in `frontend/` (port 5173, proxies `/api` to 8000).

Tests (engine hand-calculations + full API flow): `cd backend && py -m pytest -q`

Admin token (data desk): `annakavach-admin` (set `ANNAKAVACH_ADMIN_TOKEN` to change).
For QR codes that phones can open, set `ANNAKAVACH_PUBLIC_URL` to the address phones can reach (e.g. `http://192.168.1.20:8000`) and start uvicorn with `--host 0.0.0.0`.

## What is inside

| Part | What it does |
| --- | --- |
| `engine/dry.py` | Moisture budget (required WVTR), season-aware shelf life integrated day by day with real monthly weather, 1,000-sample Monte Carlo (P10/P50/P90), oxygen / light / grease / seal / temperature checks, Pareto ranking, sensitivity tornado, dispatch-month and what-if analysis |
| `engine/mapsim.py` | Modified-atmosphere packaging for respiring produce: Michaelis–Menten respiration with Q10, Arrhenius film permeability, micro-perforation diffusion; vectorised search over 1,464 bag designs across the whole journey, winner re-solved with SciPy LSODA; adds a "vent on arrival" rule when the cold chain ends |
| `engine/laminate.py` | Composer: builds ~56 valid 1–3 layer laminates from 15 film grades; barrier by layers-in-series; cost, CO2e, EPR category |
| `engine/profiler.py` | Failure-mode rules + k-nearest-neighbour estimator (scikit-learn) for foods not in the library, with confidence and the neighbours it borrowed from |
| `engine/journey.py` | Route legs from origin, destination, month and transport mode |
| `engine/intake.py` | Quick-ask parser for English, Hinglish and Hindi sentences (no LLM) |
| `climate.py` | Monthly temperature and humidity per city from the Open-Meteo archive, cached |
| `pdf.py` | Converter spec sheet (PDF) with layer drawing and QR code |
| Trace pages | QR opens `/t/<code>`: spec, batch log, and a field-report form. Reports recalibrate shelf life for that food (shrunk geometric-mean correction) |
| Front end | React PWA (installable, offline shell), English / Hindi, voice input, day and night themes |

## Data honesty

Every value is tagged: *sourced* (cited), *typical* (literature / datasheet range to verify), *assumed* (measure it), *demo* (cost bands to replace with converter quotes). Film values are indicative until supplier datasheets are loaded through the data desk. The system advises; it does not certify food safety.

MVP storage is SQLite; the schema maps directly to PostgreSQL for a pilot.
