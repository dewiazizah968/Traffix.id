import { useQuery } from "@tanstack/react-query";
import { api, unwrap } from "../../lib/api";

interface Camera {
  camera_id: string;
  intersection_id: string;
  intersection_name: string;
  status: string;
  stream_url: string | null;
  detected_vehicle_count: number;
}

const useCameras = () =>
  useQuery({
    queryKey: ["cameras"],
    queryFn: () =>
      api
        .get("/api/v1/cameras")
        .then(unwrap<{ count: number; cameras: Camera[] }>),
    refetchInterval: 5000,
    select: (d) => d.cameras,
  });

const flowBadge = (n: number) => {
  if (n >= 150)
    return {
      color: "var(--red)",
      bg: "rgba(248,113,113,.1)",
      border: "rgba(248,113,113,.2)",
      label: "HEAVY",
    };
  if (n >= 80)
    return {
      color: "var(--yellow)",
      bg: "rgba(251,191,36,.1)",
      border: "rgba(251,191,36,.2)",
      label: "MOD",
    };
  return {
    color: "var(--green)",
    bg: "rgba(74,222,128,.1)",
    border: "rgba(74,222,128,.2)",
    label: "OK",
  };
};

export const CameraGrid = () => {
  const { data: cameras = [], isLoading } = useCameras();

  return (
    <div>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: 10,
        }}
      >
        <p
          style={{
            fontSize: 10,
            color: "var(--text-dim)",
            textTransform: "uppercase",
            letterSpacing: ".08em",
          }}
        >
          CCTV Live Feed ({cameras.length} kamera)
        </p>
        <span style={{ fontSize: 10, color: "var(--text-dim)" }}>simulation-state</span>
      </div>

      {isLoading ? (
        <p
          style={{
            fontSize: 12,
            color: "var(--text-dim)",
            textAlign: "center",
            padding: 20,
          }}
        >
          Loading cameras...
        </p>
      ) : (
        <div
          style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}
        >
          {cameras.map((cam) => (
            <CamCard key={cam.camera_id} cam={cam} />
          ))}
        </div>
      )}
    </div>
  );
};

const CamCard = ({ cam }: { cam: Camera }) => {
  const f = flowBadge(cam.detected_vehicle_count);
  return (
    <div
      style={{
        background: "var(--bg-card)",
        border: "1px solid #161d27",
        borderRadius: 10,
        overflow: "hidden",
      }}
    >
      {/* Feed */}
      <div
        style={{
          height: 88,
          background: "var(--bg-elevated)",
          position: "relative",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: 5,
        }}
      >
        {/* REC badge */}
        <div
          style={{
            position: "absolute",
            top: 7,
            left: 7,
            display: "flex",
            alignItems: "center",
            gap: 3,
            fontSize: 9,
            fontWeight: 700,
            color: "var(--red)",
            background: "rgba(248,113,113,.1)",
            border: "1px solid rgba(248,113,113,.2)",
            padding: "2px 6px",
            borderRadius: 4,
          }}
        >
          <span
            style={{
              width: 4,
              height: 4,
              borderRadius: "50%",
              background: "var(--red)",
              display: "inline-block",
              animation: "blink 1s infinite",
            }}
          />
          REC
        </div>
        {/* Flow badge */}
        <div
          style={{
            position: "absolute",
            top: 7,
            right: 7,
            fontSize: 9,
            fontWeight: 600,
            color: f.color,
            background: f.bg,
            border: `1px solid ${f.border}`,
            padding: "2px 6px",
            borderRadius: 4,
          }}
        >
          {f.label}
        </div>
        <span style={{ fontSize: 22, opacity: 0.12 }}>📷</span>
        <p style={{ fontSize: 9, color: "var(--text-dim)" }}>No stream URL</p>
      </div>

      {/* Info */}
      <div
        style={{
          padding: "8px 10px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <div>
          <p style={{ fontSize: 11, fontWeight: 500, color: "var(--text-secondary)" }}>
            {cam.camera_id}
          </p>
          <p style={{ fontSize: 10, color: "var(--text-dim)" }}>
            {cam.intersection_name}
          </p>
        </div>
        <div style={{ textAlign: "right" }}>
          <p style={{ fontSize: 16, fontWeight: 600, color: f.color }}>
            {cam.detected_vehicle_count}
          </p>
          <p style={{ fontSize: 9, color: "var(--text-dim)" }}>kendaraan</p>
        </div>
      </div>
    </div>
  );
};
