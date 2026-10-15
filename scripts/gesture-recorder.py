import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from tkinter import *
from PIL import Image, ImageTk
import time
from pathlib import Path


MODEL_PATH = (
    Path(__file__).resolve().parent.parent
    / "shared"
    / "models"
    / "hand_landmarker.task"
)
assert MODEL_PATH.exists(), f"Model not found: {MODEL_PATH}"

vid = cv2.VideoCapture(0)
vid.set(cv2.CAP_PROP_FRAME_WIDTH, 800)
vid.set(cv2.CAP_PROP_FRAME_HEIGHT, 600)

app = Tk()
app.bind("<Escape>", lambda e: app.quit())
label_widget = Label(app)
label_widget.pack()

options = vision.HandLandmarkerOptions(
    base_options=python.BaseOptions(model_asset_path=str(MODEL_PATH)),
    running_mode=vision.RunningMode.VIDEO,
    num_hands=2,
)
landmarker = vision.HandLandmarker.create_from_options(
    options
)  # <-- you were missing this

# pairs of landmark indices that form the hand skeleton
CONNECTIONS = mp.tasks.vision.HandLandmarksConnections.HAND_CONNECTIONS

start = time.monotonic()
last_ts = -1


def draw_hands(frame_bgr, result):
    h, w = frame_bgr.shape[:2]
    for hand in result.hand_landmarks:  # one list of 21 landmarks per hand
        pts = [(int(lm.x * w), int(lm.y * h)) for lm in hand]  # x,y are normalized 0-1
        for c in CONNECTIONS:
            cv2.line(frame_bgr, pts[c.start], pts[c.end], (0, 255, 0), 2)
        for p in pts:
            cv2.circle(frame_bgr, p, 4, (0, 0, 255), -1)


def open_camera():
    global last_ts
    ok, frame = vid.read()
    if not ok:
        label_widget.after(10, open_camera)
        return

    frame = cv2.flip(frame, 1)  # mirror so it feels natural

    # MediaPipe wants RGB, wrapped in an mp.Image
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

    # VIDEO mode needs a strictly increasing timestamp in ms
    ts = int((time.monotonic() - start) * 1000)
    if ts <= last_ts:
        ts = last_ts + 1
    last_ts = ts

    result = landmarker.detect_for_video(mp_image, ts)
    draw_hands(frame, result)

    rgba = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
    photo = ImageTk.PhotoImage(image=Image.fromarray(rgba))
    # ignore
    label_widget.photo_image = photo  # keep a reference or Tk garbage-collects it
    label_widget.configure(image=photo)
    label_widget.after(10, open_camera)


Button(app, text="Open Camera", command=open_camera).pack()
app.mainloop()
vid.release()
landmarker.close()
