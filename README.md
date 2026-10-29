# AI Parking Space Finder

The video source is fully swappable via config - so the whole system can be
built and tested on a laptop webcam or sample footage now, and pointed at
the real Lusaka pilot-site CCTV feed later with a one-line config change
(see `docs/deployment_notes.md`).

## Quick start on Windows 11

### 1. Install prerequisites
- Python 3.10 or 3.11 from [python.org](https://www.python.org/downloads/windows/)
  - **Important:** during install, tick "Add python.exe to PATH"
- Git from [git-scm.com](https://git-scm.com/download/win) (optional, if cloning via Git)

### 2. Get the project onto your machine
If using Git:
```powershell
git clone <repo-url>
cd ai-parking-finder
```
Or just unzip the provided folder and open a terminal inside it.

### 3. Create and activate a virtual environment
Open **PowerShell** in the project folder:
```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```
> If PowerShell blocks the script with an execution policy error, run this
> once: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned`
> then try activating again.

You should see `(venv)` appear at the start of your terminal prompt.

### 4. Install dependencies
```powershell
pip install -r requirements.txt
```
This installs Flask, OpenCV, Ultralytics (YOLOv8), and everything else.
It may take a few minutes the first time.

### 5. Set up environment config
```powershell
copy .env.example .env
```
The defaults in `.env` are already set to run in **mock mode** (no camera,
no trained model, no database needed) - perfect for the first "hello world" run.

### 6. Run the server
```powershell
python server\app.py
```
You should see something like:
```
[detector] No model found at detection/model/best.pt - running in MOCK MODE.
[server] Starting on http://0.0.0.0:5000
```

### 7. Open it in a browser
- Web map: [http://localhost:5000](http://localhost:5000)
- Operator dashboard: [http://localhost:5000/dashboard](http://localhost:5000/dashboard)
- Health check (plain JSON "hello world"): [http://localhost:5000/api/health](http://localhost:5000/api/health)

You should see the bay list and map pins update every second with randomly
generated occupied/free states - this confirms the whole pipeline (server,
WebSocket, map, dashboard) works end to end, even before the YOLOv8 model
is trained or a real camera is connected.

## What's mock vs real right now
| Component | Status |
|---|---|
| Flask + WebSocket server | Fully working |
| Web map + dashboard | Fully working |
| Bay occupancy detection | **Mocked** (random) until `detection/model/best.pt` exists |
| PostgreSQL logging | Optional - skipped gracefully if no database is running |
| Video source | Defaults to a sample file path; switch via `.env` |

## Running tests
```powershell
pip install pytest
python -m pytest tests\
```

## Project structure
See `docs/report/` for the full write-up, and `docs/deployment_notes.md`
for the pilot-site (Lusaka) setup steps once the Raspberry Pi is available.

```
ai-parking-finder/
├── config/           # single source of truth for video source, DB, etc.
├── detection/        # YOLOv8 detector (mock mode until model is trained)
├── data/              # sample footage + Roboflow-annotated training data
├── server/           # Flask app, WebSocket stream worker, DB logging
├── webmap/            # driver map + operator dashboard (plain HTML/JS)
├── database/          # PostgreSQL schema
├── tests/             # smoke tests
└── docs/              # deployment notes + report chapters
```
