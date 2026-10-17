import argparse
from pathlib import Path

import cv2
import mediapipe as mp
import pandas as pd
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

from features import FEATURES, frame_features


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("filename", type=str, help="video file (.mp4)")
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default=None,
        help="output folder, put it in a folder named after the sign (e.g. data/hare)",
    )
    parser.add_argument(
        "-m", "--model", type=str, default=None, help="hand_landmarker.task"
    )
    args = parser.parse_args()

    model_path = (
        Path(args.model).resolve()
        if args.model
        else Path(__file__).resolve().parent.parent
        / "shared"
        / "models"
        / "hand_landmarker.task"
    )
    file_path = Path(args.filename).resolve()
    assert file_path.exists(), f"Video not found: {file_path}"
    assert model_path.exists(), f"Model not found: {model_path}"

    output_path = Path(args.output).resolve() if args.output else file_path.parent
    output_path.mkdir(parents=True, exist_ok=True)

    vid = cv2.VideoCapture(str(file_path))
    assert vid.isOpened(), "Could not open video"
    fps = vid.get(cv2.CAP_PROP_FPS) or 30

    options = vision.HandLandmarkerOptions(
        base_options=python.BaseOptions(model_asset_path=str(model_path)),
        running_mode=vision.RunningMode.VIDEO,
        num_hands=2,
    )

    rows = []
    frame_idx = 0
    with vision.HandLandmarker.create_from_options(options) as landmarker:
        while True:
            ok, frame = vid.read()
            if not ok:
                break
            h, w = frame.shape[:2]
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            ts = int(frame_idx * 1000 / fps)  # strictly increasing
            result = landmarker.detect_for_video(mp_image, ts)

            if result.hand_landmarks:  # skip frames with no hands
                rows.append(
                    [frame_idx, ts, *frame_features(result.hand_landmarks, w, h)]
                )
            frame_idx += 1
    vid.release()

    df = pd.DataFrame(rows, columns=["frame", "ts"] + FEATURES)
    out = output_path / f"{file_path.stem}.csv"
    df.to_csv(out, index=False)

    both = int((df["n_hands"] == 2).sum())
    print(f"{frame_idx} frames, {len(df)} with hands ({both} with both) -> {out}")


if __name__ == "__main__":
    main()
