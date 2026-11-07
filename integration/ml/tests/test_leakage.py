"""Leakage checks on the frozen split (skipped until labels + split exist)."""
from pathlib import Path

import pandas as pd
import pytest

from ml.src.split import manifest_hash
from ml.src.text import p1

ML = Path(__file__).resolve().parents[1]
SPLIT = ML / "data" / "splits" / "split_manifest.csv"
CORPUS = ML / "data" / "interim" / "corpus.parquet"
LABELS = ML / "data" / "annotation" / "labels.parquet"

pytestmark = pytest.mark.skipif(not SPLIT.exists() or not LABELS.exists(), reason="split not frozen yet")


@pytest.fixture(scope="module")
def df():
    lab = pd.read_parquet(LABELS)
    return lab.merge(pd.read_csv(SPLIT)[["ann_id", "split"]], on="ann_id", validate="1:1")


def test_every_item_assigned(df):
    assert set(df.split) == {"train", "val", "test"}
    assert df.split.notna().all()


def test_no_dup_group_crosses_splits(df):
    assert (df.groupby("dup_group").split.nunique() == 1).all()


def test_no_normalized_text_overlap(df):
    norm = df.review.map(lambda t: " ".join(p1(t).split()))
    by_split = {s: set(norm[df.split == s]) for s in ("train", "val", "test")}
    assert not (by_split["train"] & by_split["test"])
    assert not (by_split["train"] & by_split["val"])
    assert not (by_split["val"] & by_split["test"])


@pytest.mark.skipif(not CORPUS.exists(), reason="corpus not built")
def test_corpus_duplicates_of_test_not_in_train(df):
    """No record in train shares a duplicate group with any record in test (across the whole corpus)."""
    corpus = pd.read_parquet(CORPUS)[["record_id", "dup_group"]]
    test_groups = set(df.dup_group[df.split == "test"])
    train_records = set(df.record_id[df.split == "train"])
    clash = corpus[corpus.dup_group.isin(test_groups) & corpus.record_id.isin(train_records)]
    assert clash.empty


def test_split_reproducible(df):
    from ml.src.split import make_split
    fresh = df.drop(columns="split").assign(split=make_split(df.drop(columns="split")).values)
    assert manifest_hash(fresh) == manifest_hash(df)
