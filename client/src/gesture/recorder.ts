import { cameraStream } from "./camera";

// NOTE: make separate script for gesture data collection
// save the HandLandmarkers instead of the image
export let isRecording = false;
let animationFrameId: number | null = null;

export const startRecording = async (): Promise<void> => {
  if (isRecording) return;

  const videoStream = await cameraStream();
  const videoTrack = videoStream.getVideoTracks()[0];
  const imageCapture = new ImageCapture(videoTrack);

  isRecording = true;

  const saveImage = async () => {
    if (!isRecording) return;

    try {
      const bitmap = await imageCapture.grabFrame();
      await saveImageBitmapAsJpeg(bitmap, `image_${Math.random()}_${performance.now()}.jpeg`);

      bitmap.close();
    } catch (error) {
      console.error("error in saving VideoStream fram as jpeg: ", error);
    }

    if (isRecording) {
      animationFrameId = requestAnimationFrame(saveImage)
    }
  }
  animationFrameId = requestAnimationFrame(saveImage)
}

export const stopRecording = (): void => {
  isRecording = false;

  if (animationFrameId !== null) {
    cancelAnimationFrame(animationFrameId);
    animationFrameId = null;
  }
}

async function saveImageBitmapAsJpeg(imageBitmap: ImageBitmap, fileName: string = 'image.jpg'): Promise<void> {
  // 1. Create an OffscreenCanvas with the bitmap's dimensions
  const canvas = new OffscreenCanvas(imageBitmap.width, imageBitmap.height);
  const ctx = canvas.getContext('2d');

  if (!ctx) {
    throw new Error('Could not get 2D context from canvas');
  }

  // 2. Draw the ImageBitmap onto the canvas
  ctx.drawImage(imageBitmap, 0, 0);

  // 3. Convert the canvas content to a JPEG Blob (0.92 is the quality setting)
  const blob = await canvas.convertToBlob({
    type: 'image/jpeg',
    quality: 0.92
  });

  // 4. Create a download link and trigger it in the browser
  const downloadUrl = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = downloadUrl;
  link.download = fileName;

  document.body.appendChild(link);
  link.click();

  // 5. Clean up the DOM and memory
  document.body.removeChild(link);
  URL.revokeObjectURL(downloadUrl);
}
