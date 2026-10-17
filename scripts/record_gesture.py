import argparse
import time
from pathlib import Path

import cv2
import mediapipe as mp
import pandas as pd
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

from features import FEATURES, frame_features

CONNECTIONS = vision.HandLandmarksConnections.HAND_CONNECTIONS


def draw_hand(frame, hand, mirror, color):
    h, w = frame.shape[:2]
    pts = [
        ((w - 1 - int(lm.x * w)) if mirror else int(lm.x * w), int(lm.y * h))
        for lm in hand
    ]
    for c in CONNECTIONS:
        cv2.line(frame, pts[c.start], pts[c.end], color, 2)
    for p in pts:
        cv2.circle(frame, p, 4, (0, 0, 255), -1)


def save_take(rows, out_dir: Path):
    if not rows:
        print("nothing to save")
        return
    out_dir.mkdir(parents=True, exist_ok=True)
    n = len(list(out_dir.glob("take_*.csv"))) + 1
    out = out_dir / f"take_{n}.csv"
    df = pd.DataFrame(rows, columns=["frame", "ts"] + FEATURES)
    df.to_csv(out, index=False)
    both = int((df["n_hands"] == 2).sum())
    print(f"saved {len(df)} frames ({both} with both hands) -> {out}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("label", help="sign being recorded, e.g. hare")
    parser.add_argument(
        "-o", "--out", default="data", help="root folder (default: data)"
    )
    parser.add_argument("-l", "--landmarker", default=None, help="hand_landmarker.task")
    parser.add_argument("-c", "--camera", type=int, default=0)
    parser.add_argument(
        "--flip",
        action="store_true",
        help="feed the model mirrored frames; must match detect.py",
    )
    parser.add_argument(
        "--both-only",
        action="store_true",
        help="only save frames where both hands are detected",
    )
    parser.add_argument(
        "--seconds",
        type=float,
        default=0,
        help="auto-stop and save a take after this many seconds (0 = manual)",
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
    out_dir = Path(args.out) / args.label

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

    recording = False
    rec_start = 0.0
    rows = []
    seen = 0  # frames seen while recording (including skipped ones)
    start, last_ts = time.monotonic(), -1

    print(f"label: {args.label}  ->  {out_dir}")
    print("SPACE = start/stop take   D = discard take   Q/Esc = quit")

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

            n_hands = len(result.hand_landmarks)
            good = n_hands == 2
            color = (0, 255, 0) if good else (0, 165, 255)  # orange = not both hands
            for hand in result.hand_landmarks:
                draw_hand(display, hand, mirror=not args.flip, color=color)

            if recording:
                seen += 1
                if n_hands > 0 and (good or not args.both_only):
                    rows.append(
                        [len(rows), ts, *frame_features(result.hand_landmarks, w, h)]
                    )
                cv2.rectangle(display, (0, 0), (w - 1, h - 1), (0, 0, 255), 8)

            # HUD
            cv2.putText(
                display,
                f"hands: {n_hands}/2",
                (20, 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.2,
                color,
                3,
            )
            cv2.putText(
                display,
                args.label,
                (20, 100),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.2,
                (255, 255, 0),
                3,
            )
            if recording:
                both = sum(1 for r in rows if r[-1] == 2)  # last column = n_hands
                pct = f"{both / len(rows):.0%}" if rows else "-"
                info = f"REC  saved {len(rows)}/{seen}  both-hands {pct}"
                if args.seconds:
                    left = max(0.0, args.seconds - (time.monotonic() - rec_start))
                    info += f"  {left:.1f}s"
                cv2.putText(
                    display,
                    info,
                    (20, 150),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 0, 255),
                    3,
                )

            cv2.imshow("record", display)
            key = cv2.waitKey(1) & 0xFF

            if key == ord(" "):
                if recording:
                    save_take(rows, out_dir)
                    rows, seen = [], 0
                else:
                    rec_start = time.monotonic()
                recording = not recording
            elif key == ord("d") and recording:
                print("take discarded")
                rows, seen, recording = [], 0, False
            elif key in (27, ord("q")):
                if recording:
                    save_take(rows, out_dir)
                break

            # auto-stop for fixed-length takes
            if (
                recording
                and args.seconds
                and time.monotonic() - rec_start >= args.seconds
            ):
                save_take(rows, out_dir)
                rows, seen, recording = [], 0, False

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
