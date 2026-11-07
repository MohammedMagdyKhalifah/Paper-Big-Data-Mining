"""Pipeline factory + metrics shared by training and evaluation (sklearn only)."""
from __future__ import annotations

import numpy as np
from sklearn.calibration import CalibratedClassifierCV
from sklearn.dummy import DummyClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score, recall_score
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.preprocessing import FunctionTransformer
from sklearn.svm import LinearSVC

from ml.src.text import preprocess_p0, preprocess_p1

SEED = 42
PREPROCESSORS = {"P0": preprocess_p0, "P1": preprocess_p1}
TOKEN = r"(?u)\b\w+\b"   # keep 1-char tokens; Arabic negations (لا، ما) are never dropped


def features(kind: str, min_df: int):
    word = lambda ng: TfidfVectorizer(analyzer="word", ngram_range=ng, min_df=min_df, token_pattern=TOKEN, sublinear_tf=True)
    char = lambda: TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), min_df=min_df, sublinear_tf=True)
    if kind == "word11":
        return word((1, 1))
    if kind == "word12":
        return word((1, 2))
    if kind == "char25":
        return char()
    if kind == "word12+char25":
        return FeatureUnion([("w", word((1, 2))), ("c", char())])
    raise ValueError(kind)


def learner(name: str, C: float, class_weight, n_min_class: int):
    if name == "lr":
        return LogisticRegression(C=C, class_weight=class_weight, max_iter=5000, random_state=SEED)
    if name == "lr_cal":   # sigmoid-calibrated LR (calibration folds drawn from train only)
        cv = max(2, min(5, n_min_class))
        return CalibratedClassifierCV(LogisticRegression(C=C, class_weight=class_weight, max_iter=5000, random_state=SEED),
                                      method="sigmoid", cv=cv)
    if name == "svc":
        cv = max(2, min(5, n_min_class))
        return CalibratedClassifierCV(LinearSVC(C=C, class_weight=class_weight, random_state=SEED),
                                      method="sigmoid", cv=cv)
    if name == "dummy":
        return DummyClassifier(strategy="most_frequent")
    raise ValueError(name)


def build(variant: str, feat: str, min_df: int, learner_name: str, C=1.0, class_weight=None, n_min_class=5):
    steps = [("pre", FunctionTransformer(PREPROCESSORS[variant]))]
    if learner_name != "dummy":
        steps.append(("tfidf", features(feat, min_df)))
    steps.append(("clf", learner(learner_name, C, class_weight, n_min_class)))
    return Pipeline(steps)


def scores(y_true, y_pred, labels):
    return {
        "macro_f1": float(f1_score(y_true, y_pred, labels=labels, average="macro", zero_division=0)),
        "recall": {str(l): float(r) for l, r in zip(labels, recall_score(y_true, y_pred, labels=labels, average=None, zero_division=0))},
    }


def ece(conf: np.ndarray, correct: np.ndarray, bins: int = 10) -> float:
    """Expected calibration error of the top-class confidence."""
    edges = np.linspace(0, 1, bins + 1)
    total = 0.0
    for lo, hi in zip(edges[:-1], edges[1:]):
        m = (conf > lo) & (conf <= hi)
        if m.any():
            total += m.mean() * abs(correct[m].mean() - conf[m].mean())
    return float(total)
