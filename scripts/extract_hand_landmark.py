import argparse
import cv2
import mediapipe as mp
import time
import tkinter as tk
from PIL import Image, ImageTk
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from pathlib import Path


VID = None
ARGS = None
APP = None

CONNECTIONS = mp.tasks.vision.HandLandmarksConnections.HAND_CONNECTIONS


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
        assert output_path.exists(), f"Output directory not found: {ARGS.output}"
        print(f"output: {ARGS.output}")
    else:
        output_path = file_path.parent
        print(f"Default output directory: {output_path}")

    vid = cv2.VideoCapture(file_path)
    vid.set(cv2.CAP_PROP_FRAME_WIDTH, 800)
    vid.set(cv2.CAP_PROP_FRAME_HEIGHT, 600)

    app = tk.Tk()
    app.bind("<Escape>", lambda e: app.quit())
    label_widget = tk.Label(app)
    label_widget.pack()

    options = vision.HandLandmarkerOptions(
        base_options=python.BaseOptions(model_asset_path=str(model_path)),
        running_mode=vision.RunningMode.VIDEO,
        num_hands=2,
    )

    landmarker = vision.HandLandmarker.create_from_options(
        options
    )  # <-- you were missing this

    read_vid(vid, label_widget, landmarker, output_path)

    app.mainloop()
    vid.release()


start = time.monotonic()
last_ts = -1
counter = 0


def read_vid(vid, label_widget, landmarker, output_path):
    global counter
    ok, frame = vid.read()
    if not ok:
        return  # or loop / quit
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
    ts = int(vid.get(cv2.CAP_PROP_POS_MSEC))
    result = landmarker.detect_for_video(mp_image, ts)
    draw_hands(frame, result)

    image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    if output_path:
        image.save(f"{output_path}/{counter}.jpeg", format="JPEG", quality=80)
    counter += 1
    photo = ImageTk.PhotoImage(image)
    label_widget.photo_image = photo
    label_widget.configure(image=photo)
    label_widget.after(10, read_vid, vid, label_widget, landmarker, output_path)


def draw_hands(frame_bgr, result):
    h, w = frame_bgr.shape[:2]
    for hand in result.hand_landmarks:  # one list of 21 landmarks per hand
        pts = [(int(lm.x * w), int(lm.y * h)) for lm in hand]  # x,y are normalized 0-1
        for c in CONNECTIONS:
            cv2.line(frame_bgr, pts[c.start], pts[c.end], (0, 255, 0), 2)
        for p in pts:
            cv2.circle(frame_bgr, p, 4, (0, 0, 255), -1)


if __name__ == "__main__":
    main()
