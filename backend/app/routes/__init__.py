"""
API route modules for Traffix.

Routers are registered centrally in app/api.py under /api/v1.

Current routers:
  - system.py       -> /api/v1/system

Planned routers:
  - predictions.py  -> /api/v1/predictions  (LSTM 15m/2h/4h)
  - cameras.py      -> /api/v1/cameras      (YOLO vehicle input)
  - recommendations.py -> /api/v1/recommendations
  - intersections.py   -> /api/v1/intersections
  - analytics.py    -> /api/v1/analytics
  - notifications.py -> /api/v1/notifications
  - weather.py      -> /api/v1/weather      (BMKG)
  - settings.py     -> /api/v1/settings
"""
