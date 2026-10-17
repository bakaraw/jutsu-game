import type { HandLandmarkerResult } from "@mediapipe/tasks-vision";
import { bus } from "../core/bus";
import { frameFeatures } from "./features";
import { loadKnn, predict } from "./knn";
import modelUrl from "@shared/models/hand_model.json?url";


const MIN_CONF = 0.6;
const MAX_DIST = 1.5; // tune with the same numbers you found using --debug in detect.py
const HOLD = 5;       // frames a sign must be held before it counts

// Listens to "hands", emits "sign" once per held sign. Returns a stop function.
export const startGestures = async (video: HTMLVideoElement): Promise<() => void> => {
  const model = await loadKnn(modelUrl);
  let current = "?";
  let streak = 0;

  const onHands = (result: HandLandmarkerResult) => {
    let label = "?";

    if (result.landmarks.length) {
      const x = frameFeatures(result.landmarks, video.videoWidth, video.videoHeight);
      const p = predict(model, x);
      if (p.confidence >= MIN_CONF && p.nearestDist <= MAX_DIST && p.label !== "none") {
        label = p.label;
      }
    }

    streak = label === current ? streak + 1 : 1;
    current = label;

    // fires exactly once when the hold threshold is reached, not every frame
    if (streak === HOLD && label !== "?") bus.emit("sign", label);
  };

  bus.on("hands", onHands);
  return () => bus.off("hands", onHands);
};
