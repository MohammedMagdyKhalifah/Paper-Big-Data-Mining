"""Exact + near-duplicate grouping (union-find) so that duplicates never cross splits."""
from __future__ import annotations

import hashlib

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer


class UnionFind:
    def __init__(self, n: int):
        self.parent = np.arange(n)

    def find(self, i: int) -> int:
        root = i
        while self.parent[root] != root:
            root = self.parent[root]
        while self.parent[i] != root:
            self.parent[i], i = root, self.parent[i]
        return root

    def union(self, a: int, b: int) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[max(ra, rb)] = min(ra, rb)


def text_hash(normalized: str) -> str:
    return hashlib.sha1(" ".join(normalized.split()).encode("utf-8")).hexdigest()[:16]


def near_duplicate_pairs(texts, threshold: float = 0.85, chunk: int = 500):
    """Yield (i, j, sim) with i < j and char_wb 3-5-gram TF-IDF cosine >= threshold."""
    vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=1, sublinear_tf=True)
    X = vec.fit_transform(texts)  # rows are L2-normalised -> dot product = cosine
    XT = X.T.tocsc()
    for start in range(0, X.shape[0], chunk):
        block = (X[start:start + chunk] @ XT).tocoo()
        keep = (block.data >= threshold) & (block.row + start < block.col)
        for r, c, v in zip(block.row[keep] + start, block.col[keep], block.data[keep]):
            yield int(r), int(c), float(v)


def group_duplicates(normalized_texts, threshold: float = 0.85):
    """Return (group_ids, near_pairs). Exact copies (same hash) and near-duplicates share a group."""
    hashes = [text_hash(t) for t in normalized_texts]
    uniq = {}
    first_of = np.empty(len(hashes), dtype=int)
    for i, h in enumerate(hashes):
        first_of[i] = uniq.setdefault(h, i)
    reps = sorted(set(first_of.tolist()))
    uf = UnionFind(len(normalized_texts))
    for i, f in enumerate(first_of):
        uf.union(i, f)
    pairs = []
    rep_texts = [normalized_texts[i] for i in reps]
    for a, b, s in near_duplicate_pairs(rep_texts, threshold):
        uf.union(reps[a], reps[b])
        pairs.append((reps[a], reps[b], s))
    roots = np.array([uf.find(i) for i in range(len(normalized_texts))])
    return roots, pairs
