import { DrawingUtils, HandLandmarker, type HandLandmarkerResult } from "@mediapipe/tasks-vision";
import { bus } from "../core/bus";

export const startRenderer = (canvas: HTMLCanvasElement, video: HTMLVideoElement): void => {
  const ctx = canvas.getContext("2d")!;
  const drawing = new DrawingUtils(ctx);
  let latest: HandLandmarkerResult | null = null;

  bus.on<HandLandmarkerResult>("hands", (result) => {
    latest = result;
  });

  const draw = () => {
    // match the canvas to the camera's real resolution
    if (video.videoWidth && canvas.width !== video.videoWidth) {
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
    }

    ctx.save();
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // mirror once: everything drawn after this is flipped together
    ctx.translate(canvas.width, 0);
    ctx.scale(-1, 1);

    ctx.drawImage(video, 0, 0, canvas.width, canvas.height); // background
    for (const landmarks of latest?.landmarks ?? []) {
      drawing.drawConnectors(landmarks, HandLandmarker.HAND_CONNECTIONS, {
        color: "#00ff88",
        lineWidth: 3,
      });
      drawing.drawLandmarks(landmarks, { color: "#ff3355", radius: 3 });
    }

    ctx.restore();
    requestAnimationFrame(draw);
  };
  requestAnimationFrame(draw);
};
