import { FilesetResolver, HandLandmarker } from "@mediapipe/tasks-vision";
import { bus } from "../core/bus";

// Keep this version the same as your installed package: run `npm ls @mediapipe/tasks-vision`
const WASM_URL = "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@1.1.0/wasm";
// The model file must be in client/public/ so the site serves it at this path
const MODEL_URL = "/models/hand_landmarker.task";

let trackerPromise: Promise<HandLandmarker> | null = null;

// Loads the model once. Every caller gets the same promise.
export const createTracker = (): Promise<HandLandmarker> => {
  if (!trackerPromise) {
    trackerPromise = FilesetResolver.forVisionTasks(WASM_URL)
      .then((vision) =>
        HandLandmarker.createFromOptions(vision, {
          baseOptions: { modelAssetPath: MODEL_URL, delegate: "GPU" },
          numHands: 2,
          runningMode: "VIDEO",
        })
      )
      .catch((error) => {
        trackerPromise = null; // failed: let the next call try again
        throw error;
      });
  }
  return trackerPromise;
};

// Runs detection on every NEW video frame and emits the result as "hands".
// Returns a function that stops the loop.
export const startTracking = async (video: HTMLVideoElement): Promise<() => void> => {
  const tracker = await createTracker();
  let running = true;
  let lastVideoTime = -1;

  const loop = () => {
    if (!running) return;
    const hasFrame = video.readyState >= HTMLMediaElement.HAVE_CURRENT_DATA;
    if (hasFrame && video.currentTime !== lastVideoTime) {
      lastVideoTime = video.currentTime;
      const result = tracker.detectForVideo(video, performance.now());
      bus.emit("hands", result);
    }
    requestAnimationFrame(loop);
  };
  requestAnimationFrame(loop);

  return () => {
    running = false;
  };
};
