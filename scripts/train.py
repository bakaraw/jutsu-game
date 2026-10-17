import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
from sklearn.neighbors import KNeighborsClassifier

from features import FEATURES


def load(root: Path) -> pd.DataFrame:
    dfs = []
    for p in root.rglob("*.csv"):
        df = pd.read_csv(p)
        if not set(FEATURES).issubset(df.columns):
            print(f"skipping (old/unknown format): {p}")
            continue
        df["label"] = p.parent.name  # data/hare/take_1.csv -> "hare"
        df["source"] = str(p)
        dfs.append(df)
    assert dfs, f"No new-format CSVs found under {root}. Re-record/re-extract first."
    return pd.concat(dfs, ignore_index=True)


def split(df: pd.DataFrame, test_frac: float):
    # chronological split per file: first part trains, last part tests.
    # random frame splits leak, since neighbouring frames are near-identical.
    train, test = [], []
    for _, g in df.sort_values("frame").groupby("source"):
        cut = int(len(g) * (1 - test_frac))
        train.append(g.iloc[:cut])
        test.append(g.iloc[cut:])
    return pd.concat(train), pd.concat(test)


def export_json(clf, path: Path):
    json.dump(
        {
            "classes": clf.classes_.tolist(),
            "k": clf.n_neighbors,
            "X": np.round(clf._fit_X, 4).tolist(),
            "y": clf._y.tolist(),
        },
        open(path, "w"),
    )
    print(f"exported -> {path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=str, help="folder containing <label>/*.csv")
    parser.add_argument("-o", "--out", type=str, default="hand_model.joblib")
    parser.add_argument("--algo", choices=["knn", "rf"], default="knn")
    parser.add_argument("-k", type=int, default=7, help="neighbors for knn")
    parser.add_argument("--test-frac", type=float, default=0.2)
    parser.add_argument(
        "--min-hands",
        type=int,
        default=1,
        choices=[1, 2],
        help="2 = train only on frames where both hands were seen",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="after the evaluation, refit on ALL data before saving",
    )
    args = parser.parse_args()

    df = load(Path(args.root))
    df = df[df["n_hands"] >= args.min_hands]
    print(df["label"].value_counts(), "\n")

    train, test = split(df, args.test_frac)

    if args.algo == "knn":
        clf = KNeighborsClassifier(n_neighbors=args.k, weights="distance", n_jobs=-1)
    else:
        clf = RandomForestClassifier(
            n_estimators=300, n_jobs=-1, class_weight="balanced", random_state=0
        )

    clf.fit(train[FEATURES].values, train["label"])
    print(classification_report(test["label"], clf.predict(test[FEATURES].values)))

    if args.full:
        clf.fit(df[FEATURES].values, df["label"])
        print("refit on all data")

    joblib.dump(clf, args.out)  # clf.classes_ holds the label names
    print(f"saved -> {args.out}")

    if args.algo == "knn":
        export_json(clf, Path(args.out).with_suffix(".json"))


if __name__ == "__main__":
    main()
