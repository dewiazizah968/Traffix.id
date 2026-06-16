"""API smoke tests for Traffix backend."""


def _data(response):
    payload = response.json()
    assert payload["success"] is True
    return payload["data"]


def test_health_and_system_status(api_client):
    health = api_client.get("/health")
    assert health.status_code == 200
    health_data = _data(health)
    assert health_data["status"] == "ok"

    status = api_client.get("/api/v1/system/status")
    assert status.status_code == 200
    status_data = _data(status)
    assert status_data["dataset_ready"] is True
    assert status_data["weather_ready"] is True
    assert status_data["simulation_active"] is False


def test_live_intersections_endpoint(api_client):
    response = api_client.get("/api/v1/intersections")
    assert response.status_code == 200
    data = _data(response)
    assert data["count"] == 4
    first = data["intersections"][0]
    assert first["intersection_id"].startswith("INT-")
    assert first["intersection_name"] == "GT MERUYA 2B"
    assert "ai_predictions" in first


def test_predictions_endpoint_fallback_safe(api_client):
    response = api_client.get("/api/v1/predictions/INT-001")
    assert response.status_code == 200
    data = _data(response)
    assert data["intersection_id"] == "INT-001"
    assert len(data["predictions"]) == 3
    assert {item["horizon"] for item in data["predictions"]} == {"15m", "2h", "4h"}
    assert all(item["source"] in {"lstm", "dataset", "heuristic"} for item in data["predictions"])


def test_recommendations_weather_and_camera_routes(api_client):
    recommendations = api_client.get("/api/v1/recommendations")
    assert recommendations.status_code == 200
    recommendation_data = _data(recommendations)
    assert recommendation_data["count"] == 4
    assert "recommended_green_seconds" in recommendation_data["recommendations"][0]

    weather = api_client.get("/api/v1/weather/current")
    assert weather.status_code == 200
    weather_data = _data(weather)
    assert weather_data["provider"] == "local-simulation"

    intersection_weather = api_client.get("/api/v1/weather/current?intersection_id=INT-001")
    assert intersection_weather.status_code == 200
    assert _data(intersection_weather)["intersection_id"] == "INT-001"

    cameras = api_client.get("/api/v1/cameras/status")
    assert cameras.status_code == 200
    camera_data = _data(cameras)
    assert "yolo_ready" in camera_data
    assert camera_data["configured_cameras"] == 12
    assert camera_data["metadata_loaded"] is True
    assert camera_data["prediction_output_loaded"] is True
    assert camera_data["prediction_output_source"] == "json"

    camera_list = api_client.get("/api/v1/cameras")
    assert camera_list.status_code == 200
    first_camera = _data(camera_list)["cameras"][0]
    assert first_camera["intersection_name"]
    assert first_camera["video_url"].startswith("/api/v1/cameras/videos/")
    assert first_camera["traffic"]["weather"]
    assert set(first_camera["predictions"]) == {"15m", "2h", "4h"}
    assert first_camera["prediction_source"] == "lstm-output-json"


def test_simulation_status_endpoint(api_client):
    response = api_client.get("/api/v1/simulation/status")
    assert response.status_code == 200
    data = _data(response)
    assert data["dataset_ready"] is True
    assert data["dataset_metadata"]["rows"] > 0
