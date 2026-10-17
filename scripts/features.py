import numpy as np

HAND_COLS = [f"{ax}{i}" for i in range(1, 21) for ax in "xyz"]  # wrist dropped
FEATURES = (
    [f"a_{c}" for c in HAND_COLS]
    + [f"b_{c}" for c in HAND_COLS]
    + ["rel_x", "rel_y", "rel_z", "n_hands"]
)


def _hand(hand, w, h):
    pts = np.array([[lm.x * w, lm.y * h, lm.z * w] for lm in hand])
    wrist = pts[0].copy()
    pts -= wrist
    scale = np.linalg.norm(pts[9]) or 1.0
    return (pts / scale)[1:].flatten(), wrist, scale


def frame_features(hand_landmarks, w, h):
    """All hands in one frame -> one 124-value vector."""
    hands = sorted(
        (_hand(hd, w, h) for hd in hand_landmarks[:2]),
        key=lambda t: t[1][0],  # leftmost wrist first
    )
    out = np.zeros(len(FEATURES))
    if not hands:
        return out
    out[:60] = hands[0][0]
    if len(hands) == 2:
        out[60:120] = hands[1][0]
        mean_scale = (hands[0][2] + hands[1][2]) / 2
        out[120:123] = (hands[1][1] - hands[0][1]) / mean_scale  # where hand B is vs A
    out[123] = len(hands)
    return out
