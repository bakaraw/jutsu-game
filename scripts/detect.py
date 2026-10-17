import argparse
import time
from collections import Counter, deque
from pathlib import Path

import cv2
import joblib
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

from features import frame_features

CONNECTIONS = vision.HandLandmarksConnections.HAND_CONNECTIONS


def draw_hand(frame, hand, mirror):
    h, w = frame.shape[:2]
    pts = [
        ((w - 1 - int(lm.x * w)) if mirror else int(lm.x * w), int(lm.y * h))
        for lm in hand
    ]
    for c in CONNECTIONS:
        cv2.line(frame, pts[c.start], pts[c.end], (0, 255, 0), 2)
    for p in pts:
        cv2.circle(frame, p, 4, (0, 0, 255), -1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--model", default="hand_model.joblib")
    parser.add_argument("-l", "--landmarker", default=None, help="hand_landmarker.task")
    parser.add_argument("-c", "--camera", type=int, default=0)
    parser.add_argument(
        "--flip",
        action="store_true",
        help="feed the model mirrored frames (only if training videos were mirrored)",
    )
    parser.add_argument("--min-conf", type=float, default=0.6)
    parser.add_argument(
        "--max-dist",
        type=float,
        default=1.5,
        help="KNN only: nearest-neighbor distance above this = unknown pose",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="print nearest-neighbor distance (for tuning --max-dist)",
    )
    args = parser.parse_args()

    task_path = (
        Path(args.landmarker)
        if args.landmarker
        else Path(__file__).resolve().parent.parent
        / "shared"
        / "models"
        / "hand_landmarker.task"
    )
    assert task_path.exists(), f"Landmarker model not found: {task_path}"

    clf = joblib.load(args.model)
    if hasattr(clf, "n_jobs"):
        clf.n_jobs = 1

    options = vision.HandLandmarkerOptions(
        base_options=python.BaseOptions(model_asset_path=str(task_path)),
        running_mode=vision.RunningMode.VIDEO,
        num_hands=2,
        min_hand_detection_confidence=0.4,
        min_hand_presence_confidence=0.4,
        min_tracking_confidence=0.4,
    )

    cap = cv2.VideoCapture(args.camera)
    assert cap.isOpened(), "Could not open camera"
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    history = deque(maxlen=7)  # one smoothing window for the whole frame
    start, last_ts = time.monotonic(), -1

    with vision.HandLandmarker.create_from_options(options) as landmarker:
        while True:
            ok, frame = cap.read()
            if not ok:
                break

            display = cv2.flip(frame, 1)
            if args.flip:
                frame = cv2.flip(frame, 1)

            h, w = frame.shape[:2]
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

            ts = max(int((time.monotonic() - start) * 1000), last_ts + 1)
            last_ts = ts
            result = landmarker.detect_for_video(mp_image, ts)

            text = "no hands"
            if result.hand_landmarks:
                x = frame_features(result.hand_landmarks, w, h).reshape(1, -1)
                probs = clf.predict_proba(x)[0]
                best = probs.argmax()
                pred = clf.classes_[best] if probs[best] >= args.min_conf else "?"

                # too far from every training sample -> not a known sign (KNN only)
                if hasattr(clf, "kneighbors"):
                    dist, _ = clf.kneighbors(x, n_neighbors=1)
                    if args.debug:
                        print(f"dist {dist[0][0]:.2f}  pred {pred}")
                    if dist[0][0] > args.max_dist:
                        pred = "?"

                # "none" class = random hands, show it as unknown
                if pred == "none":
                    pred = "?"

                history.append(pred)
                votes = [p for p in history if p != "?"]
                smoothed = Counter(votes).most_common(1)[0][0] if votes else "?"
                text = f"{smoothed} {probs[best]:.0%}" if smoothed != "?" else "?"

                for hand in result.hand_landmarks:
                    draw_hand(display, hand, mirror=not args.flip)
            else:
                history.clear()

            cv2.putText(
                display, text, (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 0), 4
            )
            cv2.imshow("gesture", display)
            if cv2.waitKey(1) & 0xFF in (27, ord("q")):
                break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
