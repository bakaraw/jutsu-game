import { bus } from "./core/bus";
import { startCamera, disableCamera } from "./gesture/camera";
import { startTracking } from "./gesture/tracker";
import { startRenderer } from "./gesture/renderer";
import { startGestures } from "./gesture/gesture";

const video = document.querySelector<HTMLVideoElement>("#camera-stream")!;
const canvas = document.querySelector<HTMLCanvasElement>("#stage")!;
const app = document.querySelector<HTMLDivElement>("#app")!;

let stopTracking: (() => void) | null = null;
let stopGestures: (() => void) | null = null;

function stopDetection() {
  stopTracking?.();
  stopGestures?.();
  stopTracking = stopGestures = null;
}


startRenderer(canvas, video);

// register BEFORE starting the camera, so the event can't be missed
bus.on("camera:ready", async () => {
  stopDetection(); // kill any previous loop first
  try {
    stopTracking = await startTracking(video);
    stopGestures = await startGestures(video);
  } catch (error) {
    console.error("Detection failed:", error);
  }
});

bus.on("sign", (label: string) => {
  console.log("sign:", label);   // feed this into your jutsu combo logic
});

startCamera(video).catch((error) => {
  console.error("Error accessing the camera:", error);
  alert("Could not access camera. Ensure you have granted permission");
});


app.innerHTML = `
  <button id="camera-toggle">
    Toggle camera
  </button>
  <button id="recording-toggle">
    Record
  </button>
`

let cameraActive = true;
function toggleCamera() {
  if (cameraActive) {
    disableCamera();
    cameraActive = false;
    return;
  }
  startCamera(video).catch((error) => {
    console.error("Error accessing the camera:", error);
    alert("Could not access camera. Ensure you have granted permission");
  });
  cameraActive = true;
  return;
}

const disableCameraBtn = document.querySelector<HTMLButtonElement>("#camera-toggle");
disableCameraBtn?.addEventListener("click", toggleCamera);

