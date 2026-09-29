@echo off
REM Anna Kavach - one-click start (Windows). Needs Python 3.11+ and Node 18+.
cd /d %~dp0
py -m pip install -q -r backend\requirements.txt
if not exist frontend\dist\index.html (
  cd frontend
  call npm install
  call npm run build
  cd ..
)
start "" http://localhost:8000
py -m uvicorn app.main:app --port 8000 --app-dir backend
