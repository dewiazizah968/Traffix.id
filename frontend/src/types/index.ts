export interface Intersection {
  intersection_id: string;
  intersection_name: string;
  vehicle_count: number;
  avg_speed: number;
  occupancy_rate: number;
  queue_length: number;
  signal_state: "GREEN" | "YELLOW" | "RED";
  green_duration_seconds: number;
  weather_condition: string;
  ai_predictions: Record<string, number>;
  ai_insight?: string;
  ai_recommendation?: string;
  congestion_level?: string;
  yolo_source?: Record<string, any>;
  last_updated: string;
}

export interface Prediction {
  intersection_id: string;
  horizon: string;
  predicted_vehicle_count: number;
  predicted_congestion_level: string;
  confidence_score: number;
  prediction_timestamp: string;
  source: "lstm" | "dataset" | "heuristic";
}

export interface Recommendation {
  intersection_id: string;
  current_green_seconds: number;
  recommended_green_seconds: number;
  delta_seconds: number;
  reason: string;
  congestion_risk_percent: number;
  priority: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
}

export interface Weather {
  scope?: string;
  condition: string;
  temperature_celsius?: number;
  humidity_percent?: number;
  distribution?: Record<string, number>;
  intersections?: number;
  observed_at?: string;
}

export interface SystemStatus {
  service: string;
  status: string;
  ml_ready: boolean;
  ml_models_loaded: boolean;
  ml_fallback_active: boolean;
  ml_mode: string;
  weather_ready: boolean;
  simulation_ready: boolean;
  simulation_active: boolean;
  dataset_ready: boolean;
  camera_ready: boolean;
  supported_horizons: string[];
}

export interface SimulationMetrics {
  vehicle_count: number;
  avg_speed: number;
  queue_length: number;
  occupancy_rate: number;
  congestion_level: string;
}

export interface SimulationResult {
  intersection_id: string;
  current_green_seconds: number;
  proposed_green_seconds: number;
  delta_seconds: number;
  current: SimulationMetrics;
  projected: SimulationMetrics;
  improvements: {
    queue_reduction_pct: number;
    speed_gain_pct: number;
    throughput_gain_pct: number;
    occupancy_reduction_pct: number;
  };
  risk_before: number;
  risk_after: number;
  summary: string;
}
