import { useState, useEffect, useRef } from "react";
import { useQuery, useQueries, useMutation, useQueryClient } from "@tanstack/react-query";
import { api, unwrap } from "../lib/api";
import type {
  Intersection,
  Prediction,
  Recommendation,
  SimulationResult,
  Weather,
  SystemStatus,
} from "../types";

const POLL = 1000;

export const useSystemStatus = () =>
  useQuery({
    queryKey: ["system-status"],
    queryFn: () => api.get("/api/v1/system/status").then(unwrap<SystemStatus>),
    refetchInterval: POLL,
  });

export const useIntersections = () =>
  useQuery({
    queryKey: ["intersections"],
    queryFn: () =>
      api
        .get("/api/v1/intersections")
        .then(unwrap<{ count: number; intersections: Intersection[] }>),
    refetchInterval: POLL,
    select: (d) => d.intersections,
  });

export const usePredictions = (intersectionId: string) =>
  useQuery({
    queryKey: ["predictions", intersectionId],
    queryFn: () =>
      api
        .get(`/api/v1/predictions/${intersectionId}`)
        .then(
          unwrap<{
            predictions: Prediction[];
            ml_mode: string;
            ml_fallback_active: boolean;
            ml_models_loaded: boolean;
          }>,
        ),
    refetchInterval: POLL,
    enabled: !!intersectionId,
  });

export const useRecommendations = () =>
  useQuery({
    queryKey: ["recommendations"],
    queryFn: () =>
      api
        .get("/api/v1/recommendations")
        .then(unwrap<{ count: number; recommendations: Recommendation[] }>),
    refetchInterval: POLL,
    select: (d) => d.recommendations,
  });

export const useSimulation = (
  intersectionId: string | null,
  enabled: boolean,
) =>
  useQuery({
    queryKey: ["simulation", intersectionId],
    queryFn: () =>
      api
        .get(`/api/v1/recommendations/${intersectionId}/simulate`)
        .then(unwrap<SimulationResult>)
        .catch(() => null),
    refetchInterval: 2000,
    enabled: enabled && !!intersectionId,
    retry: false,
  });

export const useWeather = () =>
  useQuery({
    queryKey: ["weather"],
    queryFn: () => api.get("/api/v1/weather/current").then(unwrap<Weather>),
    refetchInterval: 30000,
  });

export const useWeatherByIntersection = (intersectionId: string) =>
  useQuery({
    queryKey: ["weather", intersectionId],
    queryFn: () =>
      api
        .get(`/api/v1/weather/current?intersection_id=${intersectionId}`)
        .then(unwrap<Weather>),
    refetchInterval: 30000,
    enabled: !!intersectionId,
  });

export const useCameraByIntersection = (intersectionId: string) =>
  useQuery({
    queryKey: ["camera", intersectionId],
    queryFn: () =>
      api
        .get("/api/v1/cameras")
        .then(unwrap<{ count: number; cameras: any[] }>)
        .then((d) =>
          d.cameras.find((c: any) => c.intersection_id === intersectionId),
        ),
    refetchInterval: 5000,
    enabled: !!intersectionId,
  });

export const useCameraByVideo = (videoUrl: string | null) =>
  useQuery({
    queryKey: ["camera-by-video", videoUrl],
    queryFn: () => {
      if (!videoUrl) return null;
      let filename = videoUrl.split("/").pop() || "";
      filename = filename.replace("converted_detected_", "");
      return api
        .get(`/api/v1/cameras/by-video/${filename}`)
        .then(unwrap<any>)
        .catch(() => null);
    },
    refetchInterval: POLL,
    enabled: !!videoUrl,
    retry: false,
  });

export const useAllCamerasByVideo = (videoUrls: (string | null)[]) => {
  const queries = useQueries({
    queries: videoUrls.map((url) => ({
      queryKey: ["camera-by-video", url],
      queryFn: () => {
        if (!url) return null;
        let filename = url.split("/").pop() || "";
        filename = filename.replace("converted_detected_", "");
        return api
          .get(`/api/v1/cameras/by-video/${filename}`)
          .then(unwrap<any>)
          .catch(() => null);
      },
      refetchInterval: POLL,
      enabled: !!url,
      retry: false,
    })),
  });
  return queries.map((q) => q.data).filter(Boolean);
};

export const useSimulationControls = () => {
  const qc = useQueryClient();
  const invalidate = () => {
    qc.invalidateQueries({ queryKey: ["system-status"] });
    qc.invalidateQueries({ queryKey: ["intersections"] });
  };

  const start = useMutation({
    mutationFn: () => api.post("/api/v1/simulation/start"),
    onSuccess: invalidate,
  });

  const stop = useMutation({
    mutationFn: () => api.post("/api/v1/simulation/stop"),
    onSuccess: invalidate,
  });

  return { start, stop };
};

export const useManualOverride = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      intersectionId,
      greenDurationSeconds,
      durationMinutes = 5,
    }: {
      intersectionId: string;
      greenDurationSeconds: number;
      durationMinutes?: number;
    }) =>
      api.post(`/api/v1/intersections/${intersectionId}/manual-override`, {
        green_duration_seconds: greenDurationSeconds,
        duration_minutes: durationMinutes,
      }).catch((err) => { throw err; }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["intersections"] });
    },
  });
};

export const useClearManualOverride = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (intersectionId: string) =>
      api.delete(`/api/v1/intersections/${intersectionId}/manual-override`)
        .catch((err) => { throw err; }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["intersections"] });
    },
  });
};

// Notifikasi dari perubahan intersection state
export interface Notification {
  id: string;
  type: "warning" | "critical" | "info" | "success";
  message: string;
  intersection_id?: string;
  timestamp: string;
  read: boolean;
}

export const useNotifications = () => {
  const { data: intersections = [] } = useIntersections();
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const prevRef = useRef<Record<string, number>>({});

  useEffect(() => {
    if (!intersections.length) return;
    const newNotifs: Notification[] = [];

    intersections.forEach((ix) => {
      const prev = prevRef.current[ix.intersection_id];
      const curr = ix.occupancy_rate;

      if (prev !== undefined) {
        if (curr >= 0.75 && prev < 0.75) {
          newNotifs.push({
            id: `${ix.intersection_id}-${Date.now()}`,
            type: "critical",
            message: `Kemacetan kritis terdeteksi di ${ix.intersection_name}`,
            intersection_id: ix.intersection_id,
            timestamp: new Date().toISOString(),
            read: false,
          });
        } else if (curr >= 0.45 && prev < 0.45) {
          newNotifs.push({
            id: `${ix.intersection_id}-${Date.now()}`,
            type: "warning",
            message: `Kemacetan sedang terdeteksi di ${ix.intersection_name}`,
            intersection_id: ix.intersection_id,
            timestamp: new Date().toISOString(),
            read: false,
          });
        } else if (curr < 0.45 && prev >= 0.45) {
          newNotifs.push({
            id: `${ix.intersection_id}-${Date.now()}`,
            type: "success",
            message: `Lalu lintas kembali normal di ${ix.intersection_name}`,
            intersection_id: ix.intersection_id,
            timestamp: new Date().toISOString(),
            read: false,
          });
        }
      }
      prevRef.current[ix.intersection_id] = curr;
    });

    if (newNotifs.length) {
      setNotifications((prev) => [...newNotifs, ...prev].slice(0, 20));
    }
  }, [intersections]);

  const markAllRead = () =>
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));

  const unreadCount = notifications.filter((n) => !n.read).length;

  return { notifications, markAllRead, unreadCount };
};
