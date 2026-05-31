# Traffix Backend Architecture

Traffix is an AI-powered smart traffic management backend built with FastAPI.
The current foundation prepares the backend for LSTM prediction, YOLO vehicle
detection, runtime simulation, weather enrichment, recommendations, analytics,
and realtime dashboard updates.

## Backend Structure

```text
backend/
├── app/
│   ├── api.py              # Central /api/v1 router registry
│   ├── main.py             # FastAPI app factory, middleware, handlers
│   ├── middleware.py       # Request tracing and request logging
│   ├── state_store.py      # In-memory runtime state singleton
│   └── routes/
│       └── system.py       # System metadata/status endpoints
├── core/
│   ├── config.py           # pydantic-settings config
│   ├── constants.py        # Shared constants and supported horizons
│   ├── exceptions.py       # Custom API exceptions
│   ├── logger.py           # Domain logger access
│   ├── logging_config.py   # Console/file logging setup
│   ├── request_context.py  # Request ID utilities
│   ├── responses.py        # Standard response envelope builders
│   ├── schemas.py          # API response schemas
│   └── state_models.py     # Runtime state Pydantic models
├── ml/                     # Future LSTM model loading and preprocessing
├── sim/                    # Future simulation engine
├── rec/                    # Future recommendation engine
├── weather/                # Future BMKG integration
├── data/                   # Runtime data mount point
├── artifacts/              # ML artifact mount point
├── logs/                   # Runtime log output
└── scripts/
    └── run_dev.py          # Local Uvicorn launcher
```

## API Architecture

The FastAPI instance is created in `app/main.py` through `create_app()`. The
app registers:

- CORS middleware for development.
- Request tracking middleware for `X-Request-ID` and `X-Process-Time`.
- Global exception handlers for validation, HTTP, custom API, and generic
  server errors.
- Centralized `/api/v1` routing from `app/api.py`.

All modular endpoints are registered under `/api/v1`. The current system
router exposes:

- `GET /api/v1/system/ping`
- `GET /api/v1/system/version`
- `GET /api/v1/system/status`

Legacy root endpoints remain available:

- `GET /`
- `GET /health`

All API responses use the standardized envelope:

```json
{
  "success": true,
  "message": "Request successful",
  "data": {},
  "request_id": "req_a1b2c3d4",
  "timestamp": "2026-05-27T22:37:00+00:00"
}
```

Errors use:

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": []
  },
  "request_id": "req_a1b2c3d4",
  "timestamp": "2026-05-27T22:37:00+00:00"
}
```

## Runtime State Management

`app/state_store.py` owns the singleton in-memory runtime state. It initializes
four default intersections from `core/constants.py` and stores:

- Traffic metrics
- Active recommendations
- Camera status
- AI predictions for `15m`, `2h`, and `4h`
- Signal timing
- Shared weather state

The store uses `threading.RLock` and returns deep copies from read methods so
future modules can safely consume state without mutating it accidentally.

## ML Integration Flow

The ML integration is intentionally stubbed in this foundation. The planned
flow is:

1. ML artifacts are mounted in `artifacts/`.
2. Paths are configured through `.env` and loaded by `core/config.py`.
3. `ml/model_loader.py` validates and loads LSTM models and scaler artifacts.
4. `ml/preprocess.py` transforms runtime traffic state into model-ready
   sequences.
5. Prediction results update `RuntimeStateStore.ai_predictions`.
6. API and websocket consumers read predictions from the state store.

Supported horizons are centralized in `core/constants.py` as `15m`, `2h`, and
`4h`.

## YOLO Integration Flow

The YOLO pipeline is also intentionally stubbed for this foundation. The
planned flow is:

1. Camera or uploaded frame input is accepted by a future camera route.
2. YOLO inference produces vehicle counts per camera/intersection.
3. Counts update `CameraState` and `TrafficMetrics`.
4. Simulation and recommendation modules consume the updated runtime state.
5. Dashboard clients receive current vehicle counts through REST or websocket.

## Weather Integration Flow

Weather integration will use the BMKG API URL configured in `.env`. A future
weather service will normalize weather payloads into `WeatherState` and update
the shared state store through `set_weather()`.

## Recommendation Flow

The recommendation engine will combine:

- Current traffic metrics
- LSTM predictions
- Weather state
- Camera status
- Safety rules

The result will update `RecommendationState` for each intersection. Business
logic is intentionally out of scope for the foundation blocks.

## Future Websocket Flow

The runtime store is designed as the backend source of truth for realtime
updates. A future websocket module can:

1. Subscribe clients to dashboard channels.
2. Read snapshots from `RuntimeStateStore`.
3. Broadcast state changes after simulation ticks, YOLO updates, or prediction
   refreshes.
4. Include request or correlation IDs in logs for observability.

The current state store remains in-memory only. Persistent storage can be added
later behind a repository or service boundary without changing the public API
response contract.
