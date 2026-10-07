import { type HandLandmarkerResult } from "@mediapipe/tasks-vision";

type Landmark = {
  x: number;
  y: number;
  z: number;
};

export const normalizeHandLandmarker = (result: HandLandmarkerResult): Landmark[][] => {
  return result.landmarks.map(hand => normalizeHand(hand));
};

const normalizeHand = (landmarks: Landmark[]): Landmark[] => {
  const values = landmarks.flatMap(({ x, y, z }) => [x, y, z]);

  const min = Math.min(...values);
  const max = Math.max(...values);

  const variation = 1 / (max - min);

  return landmarks.map(({ x, y, z }) => ({
    x: Math.round((x - min) * variation * 100) / 100,
    y: Math.round((y - min) * variation * 100) / 100,
    z: Math.round((z - min) * variation * 100) / 100,
  }));
};
