import { bus } from "./core/bus";
import { startCamera, cameraStream, disableCamera } from "./gesture/camera";
import { startTracking } from "./gesture/tracker";
import { startRenderer } from "./gesture/renderer";

const video = document.querySelector<HTMLVideoElement>("#camera-stream")!;
const canvas = document.querySelector<HTMLCanvasElement>("#stage")!;
const app = document.querySelector<HTMLDivElement>("#app")!;

startRenderer(canvas, video);

// register BEFORE starting the camera, so the event can't be missed
bus.on("camera:ready", () => {
  startTracking(video).catch((error) => console.error("Tracker failed:", error));
});

let stream = await cameraStream();
const [track] = stream.getVideoTracks();
console.log(track.getSettings());      // real width, height, frameRate
console.log(track.getCapabilities());  // what this camera can do

startCamera(video).catch((error) => {
  console.error("Error accessing the camera:", error);
  alert("Could not access camera. Ensure you have granted permission");
});


app.innerHTML = `
  <button id="camera-toggle">
    Toggle camera
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
