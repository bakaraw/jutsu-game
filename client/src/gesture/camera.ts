import { bus } from "../core/bus";

let streamPromise: Promise<MediaStream> | null = null;

// Opens the camera once. Every caller gets the same promise.
export const cameraStream = (): Promise<MediaStream> => {
  if (!streamPromise) {
    streamPromise = navigator.mediaDevices
      .getUserMedia({ video: { width: 640, height: 480, frameRate: { ideal: 60 } }, audio: false })
      .catch((error) => {
        streamPromise = null; // failed: let the next call try again
        throw error;
      });
  }
  return streamPromise;
};

// Shows the camera in a <video> and announces it when it's really ready.
export const startCamera = async (video: HTMLVideoElement): Promise<void> => {
  const stream = await cameraStream();
  video.srcObject = stream;
  await video.play();
  bus.emit<MediaStream>("camera:ready", stream);
};

export const disableCamera = async (video?: HTMLVideoElement): Promise<void> => {
  if (!streamPromise) return;
  const pending = streamPromise;
  streamPromise = null;
  const stream = await pending.catch(() => null);
  stream?.getTracks().forEach((track) => track.stop());
  if (video) video.srcObject = null;
  bus.emit("camera:stopped", undefined);
}

