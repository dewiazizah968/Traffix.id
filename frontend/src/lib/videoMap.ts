const getVideoSession = (): "pagi" | "siang" | "malam" => {
  const hour = new Date().getHours();
  if (hour >= 6 && hour < 12) return "pagi";
  if (hour >= 12 && hour < 18) return "siang";
  return "malam";
};

// Semua video per sesi — nama file sesuai hasil deteksi YOLO
const VIDEO_FILES: Record<string, string[]> = {
  pagi: [
    "detected_pagi_cctv_001_20260518_070935.mp4",
    "detected_pagi_cctv_002_20260518_070954.mp4",
    "detected_pagi_cctv_003_20260614_080117.mp4",
    "detected_pagi_cctv_004_20260518_071356.mp4",
    "detected_pagi_cctv_005_20260614_080139.mp4",
    "detected_pagi_cctv_006_20260518_071450.mp4",
    "detected_pagi_cctv_007_20260614_080221.mp4",
    "detected_pagi_cctv_008_20260614_083937.mp4",
    "detected_pagi_cctv_009_20260518_071625.mp4",
    "detected_pagi_cctv_010_20260614_084252.mp4",
    "detected_pagi_cctv_011_20260614_090616.mp4",
    "detected_pagi_cctv_012_20260614_090310.mp4",
    "detected_pagi_cctv_013_20260614_081117.mp4",
    "detected_pagi_cctv_014_20260518_072255.mp4",
    "detected_pagi_cctv_015_20260518_072703.mp4",
    "detected_pagi_cctv_016_20260614_084327.mp4",
  ],
  siang: [
    "detected_siang_cctv_001_20260518_163906.mp4",
    "detected_siang_cctv_002_20260614_163126.mp4",
    "detected_siang_cctv_003_20260518_165921.mp4",
    "detected_siang_cctv_004_20260518_170659.mp4",
    "detected_siang_cctv_005_20260518_171425.mp4",
    "detected_siang_cctv_006_20260614_170915.mp4",
    "detected_siang_cctv_007_20260518_160452.mp4",
    "detected_siang_cctv_009_20260614_170730.mp4",
    "detected_siang_cctv_010_20260614_171050.mp4",
    "detected_siang_cctv_011_20260614_171352.mp4",
    "detected_siang_cctv_012_20260614_165224.mp4",
    "detected_siang_cctv_013_20260614_171437.mp4",
    "detected_siang_cctv_016_20260614_171739.mp4",
    "detected_siang_cctv_017_20260614_171746.mp4",
    "detected_siang_cctv_018_20260614_171903.mp4",
    "detected_siang_cctv_019_20260614_172002.mp4",
  ],
  malam: [
    "detected_malam_cctv_002_20260612_233917.mp4",
    "detected_malam_cctv_003_20260518_004022.mp4",
    "detected_malam_cctv_004_20260613_224239.mp4",
    "detected_malam_cctv_005_20260518_004357.mp4",
    "detected_malam_cctv_006_20260613_202709.mp4",
    "detected_malam_cctv_007_20260518_033146.mp4",
    "detected_malam_cctv_008_20260518_004504.mp4",
    "detected_malam_cctv_009_20260518_004524.mp4",
    "detected_malam_cctv_011_20260613_224301.mp4",
    "detected_malam_cctv_012_20260613_002431.mp4",
    "detected_malam_cctv_013_20260613_224644.mp4",
    "detected_malam_cctv_014_20260518_033116.mp4",
    "detected_malam_cctv_015_20260613_224732.mp4",
    "detected_malam_cctv_016_20260518_033544.mp4",
    "detected_malam_cctv_017_20260613_225035.mp4",
    "detected_malam_cctv_018_20260613_225338.mp4",
  ],
};

// Mapping intersection ke index video + rotate setiap 3 menit
const INTERSECTION_BASE: Record<string, number> = {
  "INT-001": 0,
  "INT-002": 1,
  "INT-003": 2,
  "INT-004": 3,
};

const BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export const getVideoUrl = (intersectionId: string): string | null => {
  const session = getVideoSession();
  const files = VIDEO_FILES[session];
  if (!files?.length) return null;

  const base = INTERSECTION_BASE[intersectionId] ?? 0;

  // Rotate every 3 minutes but jump by 4 to guarantee no overlap between the 4 cameras
  // even if there is a slight millisecond drift during React re-renders.
  const rotateIndex = Math.floor(Date.now() / (3 * 60 * 1000));
  const index = (base + rotateIndex * 4) % files.length;

  return `${BASE_URL}/api/v1/cameras/videos/${session}/${files[index]}`;
};

export const getCurrentSession = () => getVideoSession();
