import argparse
import cv2
import mediapipe as mp
import time
import pandas as pd
import numpy as np
from PIL import Image, ImageTk
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from pathlib import Path


VID = None
ARGS = None
APP = None

CONNECTIONS = mp.tasks.vision.HandLandmarksConnections.HAND_CONNECTIONS
extracted_landmarks = []

cols = ["frame", "ts", "hand", "handedness"] + [
    f"{axis}{i}" for i in range(21) for axis in "xyz"
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("model", type=str, help="Model location")
    parser.add_argument("filename", type=str, help="filename of the .mp4 file")
    parser.add_argument(
        "-o", "--output", type=str, help="Output location, default filename directory"
    )

    ARGS = parser.parse_args()
    model_path = (
        Path(__file__).resolve().parent.parent
        / "shared"
        / "models"
        / "hand_landmarker.task"
    )

    file_path = Path(ARGS.filename).resolve()
    assert file_path.exists(), f"Filename not found: {ARGS.filename}"
    assert model_path.exists(), f"Model not found: {ARGS.model}"

    print(f"filename: {file_path}")

    if ARGS.output:
        output_path = Path(ARGS.output).resolve()
        if not output_path.exists():
            output_path.mkdir()
        assert output_path.exists(), f"Output directory not found: {ARGS.output}"
        print(f"output: {ARGS.output}")
    else:
        output_path = file_path.parent
        print(f"Default output directory: {output_path}")

    vid = cv2.VideoCapture(file_path)
    assert vid.isOpened(), "Could not open video"
    fps = vid.get(cv2.CAP_PROP_FPS) or 30
    vid.set(cv2.CAP_PROP_FRAME_WIDTH, 800)
    vid.set(cv2.CAP_PROP_FRAME_HEIGHT, 600)

    options = vision.HandLandmarkerOptions(
        base_options=python.BaseOptions(model_asset_path=str(model_path)),
        running_mode=vision.RunningMode.VIDEO,
        num_hands=2,
    )

    landmarker = vision.HandLandmarker.create_from_options(options)
    rows = []
    frame_idx = 0
    while True:
        ok, frame = vid.read()
        if not ok:
            break
        h, w = frame.shape[:2]
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        ts = int(frame_idx * 1000 / fps)  # strictly increasing
        result = landmarker.detect_for_video(mp_image, ts)

        for hand_idx, hand in enumerate(result.hand_landmarks):
            handedness = result.handedness[hand_idx][0].category_name
            pts = np.array([[lm.x * w, lm.y * h, lm.z * w] for lm in hand])

            pts -= pts[0]
            scale = np.linalg.norm(pts[9])

            if scale > 0:
                pts /= scale

            rows.append((frame_idx, ts, hand_idx, handedness, *pts.flatten()))
        frame_idx += 1
    vid.release()
    df = pd.DataFrame(rows, columns=cols)
    out = output_path / "landmarking.csv"
    df.to_csv(out, index=False)
    print(f"{frame_idx} frames, {len(df)} rows -> {out}")


if __name__ == "__main__":
    main()
