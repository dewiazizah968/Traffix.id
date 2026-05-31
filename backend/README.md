# Traffix Backend

AI-powered smart traffic management backend built with FastAPI. The backend
is prepared to integrate with LSTM multi-horizon prediction models (15m, 2h,
4h), a YOLO vehicle detection pipeline, BMKG weather data, and a real-time
simulation engine.

Block 0.0 initializes repository foundations only. It does not load ML models,
run simulation ticks, call weather services, or execute YOLO inference yet.

## Engineering Docs

- `ARCHITECTURE.md` - backend architecture and future integration flows
- `CONTRIBUTING.md` - branch, commit, PR, coding, and testing standards
- `PR_TEMPLATE.md` - first PR template for review readiness

## Team Structure

| Team | Output | Consumed By |
|------|--------|-------------|
| ML Team | `best_lstm_*.keras`, scalers, `best_config.json` | `ml/model_loader.py` |
| Data Team | Traffic CSV, feature list | `sim/`, `ml/preprocess.py` |
| YOLO Team | Vehicle count per frame | Future `routes/cameras.py` |
| Backend Team | REST API | React frontend |

## Tech Stack

- Python 3.11+
- FastAPI 0.111.0
- Pydantic v2 + pydantic-settings
- TensorFlow/Keras for future LSTM inference
- OpenCV for future YOLO integration
- Pandas/NumPy for data processing
- Uvicorn as the ASGI server

## Quick Start

```bash
cd backend
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Install dependencies and start the development server:

```bash
pip install -r requirements.txt
cp .env.example .env
python scripts/run_dev.py
```

The API will run at `http://localhost:8000`, with Swagger UI at
`http://localhost:8000/docs`.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_NAME` | `traffix-backend` | Service name returned by health checks |
| `APP_VERSION` | `0.1.0` | Semantic API version |
| `APP_ENV` | `development` | Runtime environment name |
| `HOST` | `0.0.0.0` | Uvicorn bind host |
| `PORT` | `8000` | Uvicorn bind port |
| `LOG_LEVEL` | `info` | Uvicorn log level |
| `CORS_ORIGINS` | `*` | Comma-separated allowed CORS origins |
| `LSTM_15M_PATH` | `artifacts/best_lstm_15m.keras` | 15-minute LSTM model path |
| `LSTM_2H_PATH` | `artifacts/best_lstm_2h.keras` | 2-hour LSTM model path |
| `LSTM_4H_PATH` | `artifacts/best_lstm_4h.keras` | 4-hour LSTM model path |
| `LSTM_CONFIG_PATH` | `artifacts/best_config.json` | LSTM config artifact path |
| `FEAT_SCALER_PATH` | `artifacts/feat_scaler.joblib` | Feature scaler path |
| `TARGET_SCALER_PATH` | `artifacts/target_scalers.joblib` | Target scalers path |
| `DUMMY_DATA_PATH` | `data/hybrid_traffic_7d.csv` | Synthetic simulation dataset path |
| `TICK_INTERVAL_SECONDS` | `2` | Future simulation tick interval |
| `SIM_INTERSECTIONS` | `4` | Future simulation intersection count |
| `BMKG_API_URL` | `https://api.bmkg.go.id/publik/prakiraan-cuaca` | BMKG API URL |
| `CAMERA_INPUT_ENABLED` | `false` | Future live camera input toggle |
| `MAX_CAMERAS` | `8` | Future maximum camera streams |

## Folder Structure

```text
backend/
├── app/
│   ├── __init__.py
│   ├── api.py
│   ├── main.py
│   ├── middleware.py
│   ├── state_store.py
│   └── routes/
│       ├── __init__.py
│       └── system.py
├── core/
│   ├── __init__.py
│   ├── config.py
│   ├── constants.py
│   ├── exceptions.py
│   ├── logger.py
│   ├── logging_config.py
│   ├── request_context.py
│   ├── responses.py
│   ├── schemas.py
│   └── state_models.py
├── sim/
│   └── __init__.py
├── rec/
│   └── __init__.py
├── weather/
│   └── __init__.py
├── ml/
│   ├── __init__.py
│   ├── model_loader.py
│   └── preprocess.py
├── data/
│   ├── .gitkeep
│   └── README_data.md
├── artifacts/
│   └── .gitkeep
├── logs/
│   └── .gitkeep
├── scripts/
│   └── run_dev.py
├── ARCHITECTURE.md
├── CONTRIBUTING.md
├── PR_TEMPLATE.md
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Welcome payload with docs and health links |
| GET | `/health` | Liveness status and supported ML horizons |
| GET | `/api/v1/system/ping` | Connectivity check |
| GET | `/api/v1/system/version` | Backend/API version metadata |
| GET | `/api/v1/system/status` | Runtime capability flags |

Example standardized response:

```json
{
  "success": true,
  "message": "pong",
  "data": {
    "alive": true
  },
  "request_id": "req_a1b2c3d4",
  "timestamp": "2026-05-27T22:37:00+00:00"
}
```

## Observability

Runtime logs are written to both console and `logs/traffix.log` with rotating
file support. Available logger domains are `system`, `api`, `ml`,
`simulation`, `recommendation`, and `weather`.

Every response includes request tracing headers:

- `X-Request-ID`
- `X-Process-Time`

## Runtime State

The in-memory runtime source of truth lives in `app/state_store.py`. It
initializes four default intersections and stores traffic metrics,
recommendations, camera status, AI predictions, signal timing, and shared
weather state.

## Artifact Mount Points

The `artifacts/` directory is the mount point for ML team outputs:

- `best_lstm_15m.keras`
- `best_lstm_2h.keras`
- `best_lstm_4h.keras`
- `feat_scaler.joblib`
- `target_scalers.joblib`
- `best_config.json`

The backend reads these paths from `.env` through `core/config.py`. Model
loading will be implemented in a future ML block.
