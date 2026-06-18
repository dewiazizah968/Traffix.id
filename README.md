# Traffix.id

**AI-based traffic monitoring and prediction system** that combines **YOLOv8**-based
vehicle detection with **LSTM**-based multi-horizon traffic volume forecasting,
enriched with weather data and national public holiday indicators, served through
a **FastAPI** backend with an adaptive signal timing recommendation engine, and
visualized through a **React + TypeScript** web dashboard.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Project Directory Structure](#project-directory-structure)
3. [System Pipeline](#system-pipeline)
4. [Model Download & Loading](#model-download--loading)
5. [Frontend Application](#frontend-application)
6. [Project Dependencies](#project-dependencies)
7. [Supporting Configuration](#supporting-configuration)
8. [Environment Setup](#environment-setup)
9. [Running the Application](#running-the-application)
10. [Testing](#testing)
11. [Additional Documentation](#additional-documentation)

---

## Project Overview

Traffix.id is an AI system for monitoring and predicting urban traffic conditions
in Indonesia. It combines two core machine learning models:

- **YOLOv8 (Ultralytics)** — detects and tracks vehicles (cars, motorcycles,
  buses, trucks) from highway/road CCTV footage, then extracts traffic features
  such as vehicle count, average speed, density, and queue length.
- **LSTM (TensorFlow/Keras)** — predicts traffic volume across three simultaneous
  time horizons (**15 minutes**, **2 hours**, **4 hours**) using YOLO-derived
  features enriched with weather data and holiday/weekend indicators.

The detection and prediction results are consumed by a **FastAPI backend** that
provides a REST API for per-intersection traffic status, multi-horizon predictions,
weather context, and **rule-based adaptive green light duration recommendations**.
These results are then visualized in real time through a **React + TypeScript
web dashboard** (`frontend/`), which displays live intersection metrics, prediction
charts, an interactive map, camera feeds, and a recommendation approval workflow
for traffic operators.

Current model performance summary (see [Model Download & Loading](#model-download--loading)
for full details):

| Model | Key Metric | Value |
|---|---|---|
| YOLOv8 (vehicle detection) | Precision / Recall / F1 | 0.867 / 0.884 / 0.876 |
| YOLOv8 (vehicle detection) | mAP50 / mAP50-95 | 0.926 / 0.532 |
| LSTM — 15-minute horizon | MAPE (test set) | ≈ 21.8% |
| LSTM — 2-hour horizon | MAPE (test set) | ≈ 27.0% |
| LSTM — 4-hour horizon | MAPE (test set) | ≈ 32.5% |

This project is developed in a modular, stage-by-stage manner (data collection →
preprocessing → YOLO training → LSTM training → inference → backend API →
frontend dashboard), so each component can be run and tested independently.

## Project Directory Structure

```text
Traffix.id/
├── backend/                     # FastAPI backend (REST API, simulation, recommendations)
│   ├── app/                     # App factory, routes, services, state store
│   ├── core/                    # Config, constants, schemas, logging
│   ├── ml/                      # LSTM model loader & predictor
│   ├── sim/                     # Simulation tick engine & dataset replay
│   ├── rec/                     # Rule-based recommendation engine
│   ├── weather/                 # Weather context service
│   ├── tests/                   # Unit & integration tests (pytest)
│   ├── .env.example             # Backend environment template
│   ├── requirements.txt         # Backend dependencies
│   └── README.md / ARCHITECTURE.md / CONTRIBUTING.md
├── frontend/                     # React + TypeScript web dashboard (Vite)
│   ├── src/
│   │   ├── pages/                # Dashboard, LiveMap, Login, Settings
│   │   ├── components/
│   │   │   ├── dashboard/        # IntersectionCard, MetricCard, PredictionChart,
│   │   │   │                     # RecommendationPanel, ManualSignalAdjust, CameraGrid
│   │   │   └── layout/           # Navbar, NotificationBell
│   │   ├── hooks/useTraffixData.ts  # React Query hooks for all backend endpoints
│   │   ├── lib/                  # api.ts (Axios client), AuthContext, ThemeContext, videoMap
│   │   ├── types/index.ts        # Shared TypeScript types (mirrors backend schemas)
│   │   └── main.tsx / App.tsx
│   ├── public/                   # Static assets (logo, icons, favicon)
│   ├── package.json              # Frontend dependencies & scripts
│   └── vite.config.ts / tsconfig*.json / tailwind.config.js / eslint.config.js
├── yolo pipeline/                # YOLOv8 training pipeline
│   ├── code/                     # Training notebook (Colab)
│   ├── config/data.yaml          # YOLO dataset configuration
│   ├── model/best.pt             # Trained YOLOv8 model
│   ├── dataset/traffic_features.csv
│   └── visualization/            # Detection visualization outputs
├── LSTM Training/                 # LSTM training pipeline
│   ├── traffix_lstm_final.ipynb   # Training notebook (grid search + final model)
│   └── artifacts/                 # Model .keras, scaler .joblib, config, metrics
├── inference/                     # Production inference notebooks & results
│   ├── inference_yolo/            # YOLO inference notebook on CCTV video
│   ├── inference_lstm/            # LSTM multi-horizon inference notebook
│   └── outputs/                   # Final prediction results (CSV/JSON)
├── data/                           # Data processing & synthetic data
│   ├── data_process/               # EDA, feature engineering, data dictionary notebooks
│   ├── data_synthetic/             # Synthetic dataset generator (hybrid_traffic_7d.csv)
│   ├── cctv_stage1_collect_links.py
│   └── cctv_stage2_record_videos.py
├── inference_data/data_video/      # Pipeline for processing CCTV video into ready-to-use datasets
│   ├── 01_create_video_inventory.py … 07_fetch_weather_openmeteo.py
│   ├── frames/                     # Sample CCTV frames (morning/afternoon/night)
│   └── metadata/                   # Location metadata, coordinates, weather
├── .github/workflows/backend-ci.yml  # Backend CI test (GitHub Actions)
├── .gitignore
├── requirements.txt                 # Combined dependencies for the full pipeline (see Dependencies)
└── README.md                        # This file
```

## System Pipeline

```text
CCTV Video
   │
   ▼
[YOLOv8 + ByteTrack]  →  per-frame/video traffic features
   (vehicle detection & tracking)   (vehicle_count, avg_speed, density, queue)
   │
   ▼
[Feature Enrichment]  →  + weather data (Open-Meteo/BMKG) + public holiday calendar
   │
   ▼
[LSTM Multi-Horizon]  →  volume predictions: 15 minutes, 2 hours, 4 hours
   │
   ▼
[Rule-Based Recommendation Engine]  →  adaptive green light duration recommendations
   │
   ▼
[FastAPI Backend]  →  REST API (intersections, predictions, recommendations,
                        weather, simulation, cameras)
   │
   ▼
[React + TypeScript Frontend]  →  web dashboard (live metrics, prediction charts,
                                    interactive map, camera feeds, recommendation
                                    approval workflow)
```

In the current configuration, the backend runs a replay simulation from a
synthetic dataset (`data/data_synthetic/hybrid_traffic_7d.csv`) as its runtime
data source, while still loading the real LSTM model to generate predictions. If
the `.keras` artifacts are not found, the backend automatically falls back to
heuristic mode (`ML_ALLOW_FALLBACK=true`) to keep the API responsive.

## Model Download & Loading

Both the YOLOv8 and LSTM models are **included directly in this repository**
(no external hosting required), as their file sizes are small and within
GitHub's standard file size limits.

### 1. YOLOv8 Model (Vehicle Detection)

| File | Location in Repo | Size |
|---|---|---|
| `best.pt` | `yolo pipeline/model/best.pt` | ~6 MB |

**Direct download (without cloning):**

```bash
curl -L -o best.pt \
  "https://raw.githubusercontent.com/dewiazizah968/Traffix.id/main/yolo%20pipeline/model/best.pt"
```

**Loading the model (Python):**

```python
from ultralytics import YOLO

yolo_model = YOLO("yolo pipeline/model/best.pt")  # or local path after download
print(yolo_model.names)  # list of classes
```

This model was fine-tuned on top of `yolov8n.pt` (Ultralytics) using the
[Traffic Road Object Detection Dataset](https://www.kaggle.com/datasets/boukraailyesali/traffic-road-object-detection-dataset-using-yolo)
from Kaggle (downloaded automatically via `kagglehub` in the training notebook).
Validation set results: Precision 0.867, Recall 0.884, F1 0.876,
mAP50 0.926, mAP50-95 0.532.

### 2. LSTM Model (Multi-Horizon Prediction)

| File | Location in Repo | Description |
|---|---|---|
| `best_lstm_15m.keras` | `LSTM Training/artifacts/best_lstm_15m.keras` | 15-minute horizon model |
| `best_lstm_2h.keras` | `LSTM Training/artifacts/best_lstm_2h.keras` | 2-hour horizon model |
| `best_lstm_4h.keras` | `LSTM Training/artifacts/best_lstm_4h.keras` | 4-hour horizon model |
| `feat_scaler.joblib` | `LSTM Training/artifacts/feat_scaler.joblib` | Input feature scaler |
| `target_scalers.joblib` | `LSTM Training/artifacts/target_scalers.joblib` | Per-horizon target scaler |
| `best_config.json` | `LSTM Training/artifacts/best_config.json` | Best hyperparameter configuration |
| `feature_columns.json` | `data/data_process/feature_columns.json` | Model feature list & column order |

**Direct download (without cloning), example for the 15-minute model:**

```bash
curl -L -o best_lstm_15m.keras \
  "https://raw.githubusercontent.com/dewiazizah968/Traffix.id/main/LSTM%20Training/artifacts/best_lstm_15m.keras"
curl -L -o feat_scaler.joblib \
  "https://raw.githubusercontent.com/dewiazizah968/Traffix.id/main/LSTM%20Training/artifacts/feat_scaler.joblib"
curl -L -o target_scalers.joblib \
  "https://raw.githubusercontent.com/dewiazizah968/Traffix.id/main/LSTM%20Training/artifacts/target_scalers.joblib"
curl -L -o best_config.json \
  "https://raw.githubusercontent.com/dewiazizah968/Traffix.id/main/LSTM%20Training/artifacts/best_config.json"
```

Replace `best_lstm_15m.keras` in the URL above with `best_lstm_2h.keras` or
`best_lstm_4h.keras` to download the other horizon models.

**Loading the model (Python):**

```python
import json
import joblib
from tensorflow.keras.models import load_model

# Configuration & scalers
with open("LSTM Training/artifacts/best_config.json") as f:
    config = json.load(f)

feat_scaler = joblib.load("LSTM Training/artifacts/feat_scaler.joblib")
target_scalers = joblib.load("LSTM Training/artifacts/target_scalers.joblib")

# Per-horizon models
model_15m = load_model("LSTM Training/artifacts/best_lstm_15m.keras")
model_2h  = load_model("LSTM Training/artifacts/best_lstm_2h.keras")
model_4h  = load_model("LSTM Training/artifacts/best_lstm_4h.keras")
```

Current best configuration (`best_config.json`): `seq_len=15`,
`feature_scaler=standard`, `target_scaler=standard`, `learning_rate=0.001`,
`batch_size=32`, `dropout=0.1`, `loss=mae`, `arch=lstm_light`, with a 15-minute
test set MAPE of ≈ 21.8%.

> Note: the backend reads the model paths above automatically via
> `backend/.env` (see [Supporting Configuration](#supporting-configuration)),
> so after a full repo clone, **no manual download step is required** —
> the backend reads these artifacts directly from the `LSTM Training/artifacts/` folder.

## Frontend Application

`frontend/` is a **React 19 + TypeScript** single-page application, bundled
with **Vite** and styled with **Tailwind CSS**, that serves as the operator-facing
web dashboard for Traffix.id. It consumes the FastAPI backend's REST API
(see [Running the Backend API](#1-running-the-backend-api-fastapi)) and
polls it continuously (every 1 second for live traffic data, every 30 seconds
for weather) to render an up-to-date view of intersection conditions.

**Key libraries:**

| Library | Purpose |
|---|---|
| `@tanstack/react-query` | Data fetching, caching, and polling for all backend endpoints |
| `axios` | HTTP client (`src/lib/api.ts`), base URL configurable via `VITE_API_URL` |
| `react-leaflet` / `leaflet` | Interactive map on the Live Map page |
| `recharts` | LSTM multi-horizon prediction line charts |
| `tailwindcss` | Utility-first styling (combined with CSS-variable-based theming) |

**Pages (`src/pages/`):**

- **Login** — entry screen with a client-side dummy authentication (stored in
  `localStorage`, no backend auth endpoint involved). Default demo credentials:
  username `admin`, password `admin123`.
- **Dashboard** — main operator view: aggregate KPI cards (total vehicles,
  average speed, active intersections), per-intersection cards, LSTM
  multi-horizon prediction charts, the AI recommendation approval panel, a
  manual signal override control, and a live camera feed grid.
- **Live Map** — Leaflet map plotting the four monitored intersections with
  color-coded congestion and signal-state badges.
- **Settings** — displays backend system status (ML/weather/simulation/camera
  readiness) and exposes simulation start/stop controls.

**Notable components (`src/components/`):**

- `layout/Navbar.tsx` — page navigation tabs, live "Operational/Idle" status
  pill, notification bell, dark/light theme toggle, and logout control.
- `layout/NotificationBell.tsx` — surfaces client-derived alerts (e.g.
  congestion threshold crossings) computed from polled intersection data.
- `dashboard/RecommendationPanel.tsx` — approve/reject/simulate workflow for
  AI-generated green-light duration recommendations.
- `dashboard/ManualSignalAdjust.tsx` — manual green-light duration override
  per intersection, calling the backend's manual-override endpoints.
- `dashboard/PredictionChart.tsx` / `CameraGrid.tsx` / `IntersectionCard.tsx` /
  `MetricCard.tsx` — prediction visualization, camera feed display, and
  per-intersection/aggregate metric displays.

**Configuration:** the only environment variable used is `VITE_API_URL`
(defaults to `http://localhost:8000` if unset), which points the frontend to
the FastAPI backend. There is currently no `.env.example` file for the
frontend, so set this directly in a `frontend/.env` file (e.g.
`VITE_API_URL=http://localhost:8000`) if the backend runs on a different host
or port.

> See [Running the Frontend](#2-running-the-frontend-web-dashboard) for setup
> and run instructions.

## Project Dependencies

This project has two dependency stacks: a **Python** stack for the data
processing pipeline, YOLO/LSTM notebooks, and the FastAPI backend, and a
**Node.js** stack for the React frontend.

**Python dependencies** are managed via `requirements.txt` files:

| File | Scope | When to use |
|---|---|---|
| `requirements.txt` (root) | Full pipeline: backend, data processing, YOLO, LSTM | Running the complete pipeline locally |
| `backend/requirements.txt` | Backend API only | Running or developing only the backend |

Notebooks (`.ipynb`) in Google Colab install their own dependencies via
`!pip install ...` cells at the beginning of each notebook, so the
`requirements.txt` files above are primarily needed when running the pipeline
**locally** (not in Colab).

**Node.js dependencies** for the frontend are managed via `frontend/package.json`
(see [Frontend Application](#frontend-application) for the key libraries used).
Install them with `npm install` inside `frontend/` — see
[Environment Setup](#environment-setup) for the full setup flow.

Non-Python system-level dependencies required for the CCTV video data collection stage:

- **ffmpeg** — frame extraction & video stream recording (`data/cctv_stage2_record_videos.py`,
  `inference_data/data_video/02_extract_frames.py`).
- **Playwright browser binaries** — CCTV link scraping (`data/cctv_stage1_collect_links.py`),
  installed via `playwright install`.

## Supporting Configuration

| File | Location | Purpose |
|---|---|---|
| `.gitignore` | root | Ignores Python cache, virtual environments, logs, temporary outputs (video/CCTV), and `frontend/node_modules` across the full pipeline |
| `backend/.gitignore` | `backend/` | Ignores `.env`, ML artifacts (`*.keras`, `*.joblib`), and large CSV datasets inside the backend folder |
| `backend/.env.example` | `backend/` | Backend environment variable template (see setup section below) |
| `backend/pytest.ini` | `backend/` | pytest configuration (test paths, asyncio mode) |
| `frontend/vite.config.ts` | `frontend/` | Vite build/dev server configuration (React plugin) |
| `frontend/tsconfig*.json` | `frontend/` | TypeScript compiler configuration (app + Node split configs) |
| `frontend/tailwind.config.js` / `postcss.config.js` | `frontend/` | Tailwind CSS content scanning & PostCSS pipeline |
| `frontend/eslint.config.js` | `frontend/` | ESLint rules (React Hooks, React Refresh, TypeScript-ESLint) |
| `.github/workflows/backend-ci.yml` | `.github/workflows/` | Automated CI: install dependencies & run backend tests on every push/PR |

## Environment Setup

### 1. Clone the Repository

```bash
git clone https://github.com/dewiazizah968/Traffix.id.git
cd Traffix.id
```

### 2. Create a Python Virtual Environment (Python 3.11+ recommended)

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate
```

### 3. Install Backend / Pipeline Dependencies (Python)

To run the **full pipeline** (data processing, YOLO, LSTM, backend) locally:

```bash
pip install -r requirements.txt
```

To run only the **backend API**:

```bash
cd backend
pip install -r requirements.txt
```

### 4. Install Frontend Dependencies (Node.js)

Requires **Node.js 20.19+ or 22.12+** (the version range required by Vite 8).

```bash
cd frontend
npm install
```

### 5. Configure the Backend Environment File

```bash
cd backend
cp .env.example .env
```

Adjust values in `.env` if needed (e.g. `PORT`, `CORS_ORIGINS`, or model paths
if the folder structure is relocated). For local development using the default
repository folder structure, the default values in `.env.example` are correct
and do not need to be changed.

> The frontend has no `.env.example` file; it only reads one optional variable,
> `VITE_API_URL`, which defaults to `http://localhost:8000` if not set (see
> [Frontend Application](#frontend-application)).

## Running the Application

### 1. Running the Backend API (FastAPI)

```bash
cd backend
python scripts/run_dev.py
```

The backend will be available at `http://localhost:8000` with interactive Swagger
documentation at `http://localhost:8000/docs`. On startup, the backend automatically:

- loads the simulation dataset (`data/data_synthetic/hybrid_traffic_7d.csv`),
- loads the LSTM models from `LSTM Training/artifacts/` (or falls back to
  heuristics if artifacts are not found),
- starts the simulation tick engine as the runtime data source.

Main endpoint summary (full details in `backend/README.md`):

| Endpoint | Description |
|---|---|
| `GET /health` | Service health status |
| `GET /api/v1/system/status` | Runtime status (ML, simulation, dataset, cameras) |
| `GET /api/v1/intersections` | Live traffic status per intersection |
| `GET /api/v1/predictions/{intersection_id}` | 15m/2h/4h predictions for a single intersection |
| `POST /api/v1/predictions` | Prediction for a specific single horizon |
| `GET /api/v1/recommendations` | Green light duration recommendations per intersection |
| `GET /api/v1/weather/current` | Current weather context |
| `GET /api/v1/simulation/status` | Replay simulation status |
| `POST /api/v1/simulation/start` / `/stop` | Simulation controls |
| `GET /api/v1/cameras` | List of camera slots per intersection |

### 2. Running the Frontend (Web Dashboard)

Make sure the backend (step 1 above) is running first, since the frontend has
no data of its own and relies entirely on the backend's REST API.

```bash
cd frontend
npm run dev
```

The dashboard will be available at `http://localhost:5173` (Vite's default
dev server port). On first load:

1. Log in with the demo credentials: username `admin`, password `admin123`
   (this is a client-side dummy login only, not validated by the backend).
2. The **Dashboard** page loads live intersection metrics, prediction charts,
   and AI recommendations, polling the backend every 1 second.
3. Use the **Live Map** tab for a geographic view of the four monitored
   intersections, or **Settings** to check system status and start/stop the
   backend's replay simulation.

If the backend runs on a different host/port than `http://localhost:8000`,
create `frontend/.env` with `VITE_API_URL=<your-backend-url>` before starting
the dev server.

Other available scripts (run from `frontend/`):

| Command | Purpose |
|---|---|
| `npm run build` | Type-check (`tsc -b`) and build a production bundle to `frontend/dist/` |
| `npm run preview` | Preview the production build locally |
| `npm run lint` | Run ESLint over the codebase |

### 3. Running the YOLOv8 Pipeline (Training & Inference)

**Training** (rebuilding `best.pt` from scratch):

1. Open `yolo pipeline/code/traffix_yolo_pipeline_revised.ipynb` in Google
   Colab (GPU runtime recommended: *Runtime → Change runtime type → T4 GPU*).
2. Run all cells in order — the Kaggle dataset is downloaded automatically
   via `kagglehub`, so no manual upload is required.
3. Output: `best.pt`, `traffic_features.csv`, and detection visualizations.

**Inference** (running detection on CCTV video):

1. Open `inference/inference_yolo/traffix_yolo_inference.ipynb` in Colab.
2. Mount a Google Drive containing the CCTV video folder (structure:
   `data_baru/pagi`, `/siang`, `/malam`), or use the sample videos in
   `inference_data/data_video/frames/`.
3. Ensure `best.pt` and `video_weather_data.csv` are available in the
   notebook working directory.
4. Output: `vehicle_count.csv` — per-video traffic features, which serve as
   input for the LSTM inference pipeline.

### 4. Running the LSTM Pipeline (Training & Inference)

**Training:**

1. Open `LSTM Training/traffix_lstm_final.ipynb` in Colab.
2. Upload `traffix_lstm_ready.csv` and `feature_columns.json` (both located in
   `data/data_process/`) to the notebook working directory.
3. Run all cells — the notebook performs a configuration grid search on the
   15-minute horizon, then trains models for all three horizons.
4. Output: three `.keras` model files, two `.joblib` scaler files, `best_config.json`,
   and `metrics.json`, automatically bundled into a single `.zip` file for
   download (or retrievable manually from the `artifacts/` folder if not in Colab).

**Inference:**

1. Open `inference/inference_lstm/traffix_lstm_inference.ipynb` in Colab.
2. In the "Upload Artifacts" cell, upload all seven required files: three
   `.keras` models, two `.joblib` scalers, `best_config.json`, `feature_columns.json`,
   and `vehicle_count.csv` (output from YOLO inference).
3. Run all cells to generate 15-minute/2-hour/4-hour predictions along with
   AI-based insights and recommendations.
4. Output: `lstm_prediction_output.csv`/`.json` and `lstm_inference_summary.json`.

### 5. Running Data Collection & Processing Scripts

CCTV video data pipeline sequence (see `inference_data/data_video/video_data.md`
for full details):

```bash
python data/cctv_stage1_collect_links.py     # collect public CCTV stream links
python data/cctv_stage2_record_videos.py     # record video from streams
python inference_data/data_video/01_create_video_inventory.py
python inference_data/data_video/02_extract_frames.py
python inference_data/data_video/03_select_best_frame.py
python inference_data/data_video/03b_validate_location_input.py
python inference_data/data_video/04_create_unique_camera_locations.py
python inference_data/data_video/05_validate_camera_coordinates.py
python inference_data/data_video/06_join_video_with_coordinates.py
python inference_data/data_video/07_fetch_weather_openmeteo.py
```

These scripts only access public APIs (Open-Meteo, public CCTV sites from
Bina Marga PUPR) and do not require any API keys or credentials.

To generate the synthetic dataset (used by the backend as a simulation data source):

```bash
python data/data_synthetic/generate_data_hybrid.py
```

## Testing

```bash
cd backend
pytest -q
```

Backend tests also run automatically via GitHub Actions
(`.github/workflows/backend-ci.yml`) on every push or pull request that
touches the `backend/` folder.

The frontend does not yet have a dedicated test suite; static checks are run via ESLint:

```bash
cd frontend
npm run lint
```

## Additional Documentation

- `backend/ARCHITECTURE.md` — backend architecture & detailed ML/YOLO/weather integration flow.
- `backend/CONTRIBUTING.md` — branch, commit, and pull request standards.
- `data/data_process/data_dictionary.md` — data dictionary for all feature columns.
- `data/data_process/aggregation_rules.md` — synthetic data aggregation rules.
- `data/data_process/dataset_validation.md` — synthetic dataset validation notes.
- `inference_data/data_video/video_data.md` — CCTV video data processing pipeline documentation.
