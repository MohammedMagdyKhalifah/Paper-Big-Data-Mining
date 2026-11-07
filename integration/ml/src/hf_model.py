"""MARBERTv2 7-way fine-tuning (MPS) and local inference wrapper.

Input text is privacy-masked with P0 (the tokenizer handles its own normalisation). Labels: LABELS7.
Training: AdamW, linear warm-up/decay, length-sorted mini-batches, gradient accumulation, early stopping on
validation e2e macro-F1, best weights kept in memory. Temperature scaling is fitted on validation logits.
"""
from __future__ import annotations

import json
import math
import os
import random
import time
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")          # never call the network at train or inference time
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

import numpy as np
import torch

from ml.src.a4_common import LABELS7, metrics
from ml.src.text import p0

MARBERT = "UBC-NLP/MARBERTv2"
MARBERT_REV = "fe88db9db8ccdb0c4e1627495f405c44a5f89066"


def set_seed(seed: int):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def _batches(enc_lens, bs, shuffle, rng):
    """Length-bucketed batches: sort by length inside random chunks of 50 batches."""
    idx = np.arange(len(enc_lens))
    if shuffle:
        rng.shuffle(idx)
        chunk = bs * 50
        idx = np.concatenate([c[np.argsort(enc_lens[c])] for c in np.array_split(idx, max(1, len(idx) // chunk))])
        bl = [idx[i:i + bs] for i in range(0, len(idx), bs)]
        rng.shuffle(bl)
        return bl
    idx = idx[np.argsort(enc_lens)]
    return [idx[i:i + bs] for i in range(0, len(idx), bs)]


class Encoded:
    def __init__(self, tok, texts, max_len):
        enc = tok([p0(t) for t in texts], truncation=True, max_length=max_len)
        self.ids = enc["input_ids"]
        self.lens = np.array([len(x) for x in self.ids])

    def collate(self, b, device):
        L = int(self.lens[b].max())
        ids = torch.zeros((len(b), L), dtype=torch.long)
        mask = torch.zeros((len(b), L), dtype=torch.long)
        for k, i in enumerate(b):
            ids[k, :self.lens[i]] = torch.tensor(self.ids[i])
            mask[k, :self.lens[i]] = 1
        return ids.to(device), mask.to(device)


@torch.no_grad()
def predict_logits(model, enc: Encoded, device, bs=64):
    model.eval()
    out = np.zeros((len(enc.lens), model.config.num_labels), dtype=np.float32)
    for b in _batches(enc.lens, bs, False, None):
        ids, mask = enc.collate(b, device)
        out[b] = model(input_ids=ids, attention_mask=mask).logits.float().cpu().numpy()
    return out


def softmax(z, T=1.0):
    z = z / T
    z = z - z.max(1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(1, keepdims=True)


def fit_temperature(logits, y_idx):
    best, bestT = 1e9, 1.0
    for T in np.arange(0.5, 5.01, 0.05):
        p = softmax(logits, T)
        nll = -np.log(np.maximum(p[np.arange(len(y_idx)), y_idx], 1e-12)).mean()
        if nll < best:
            best, bestT = nll, float(round(T, 2))
    return bestT


def train_marbert(train_texts, train_y, val_texts, val_y, cfg: dict, log=print):
    """Return (model on cpu with best weights, history, val_logits_at_best)."""
    from transformers import AutoModelForSequenceClassification, AutoTokenizer, get_linear_schedule_with_warmup
    set_seed(cfg["seed"])
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    tok = AutoTokenizer.from_pretrained(MARBERT, revision=MARBERT_REV)
    model = AutoModelForSequenceClassification.from_pretrained(
        MARBERT, revision=MARBERT_REV, num_labels=len(LABELS7),
        id2label=dict(enumerate(LABELS7)), label2id={l: i for i, l in enumerate(LABELS7)}).to(device)
    y_tr = np.array([LABELS7.index(l) for l in train_y])
    y_va = np.array([LABELS7.index(l) for l in val_y])
    tr, va = Encoded(tok, train_texts, cfg["max_len"]), Encoded(tok, val_texts, cfg["max_len"])
    weights = None
    if cfg["loss"] == "ce_sqrt_class_weights":
        cnt = np.bincount(y_tr, minlength=len(LABELS7)).astype(float)
        w = np.sqrt(cnt.sum() / np.maximum(cnt, 1))
        weights = torch.tensor(w / w.mean(), dtype=torch.float32, device=device)
    loss_fn = torch.nn.CrossEntropyLoss(weight=weights)
    opt = torch.optim.AdamW(model.parameters(), lr=cfg["lr"], weight_decay=0.01)
    steps_per_epoch = math.ceil(len(y_tr) / cfg["batch_size"] / cfg["grad_accum"])
    sched = get_linear_schedule_with_warmup(opt, int(0.06 * steps_per_epoch * cfg["max_epochs"]), steps_per_epoch * cfg["max_epochs"])
    rng = np.random.default_rng(cfg["seed"])
    best, best_state, best_logits, bad, hist = -1.0, None, None, 0, []
    for ep in range(1, cfg["max_epochs"] + 1):
        model.train()
        t0 = time.time()
        tot = 0.0
        for k, b in enumerate(_batches(tr.lens, cfg["batch_size"], True, rng)):
            ids, mask = tr.collate(b, device)
            logits = model(input_ids=ids, attention_mask=mask).logits
            loss = loss_fn(logits, torch.tensor(y_tr[b], device=device)) / cfg["grad_accum"]
            loss.backward()
            tot += float(loss.detach()) * cfg["grad_accum"]
            if (k + 1) % cfg["grad_accum"] == 0:
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                opt.step(); sched.step(); opt.zero_grad()
        if (k + 1) % cfg["grad_accum"] != 0:      # flush a partial accumulation at epoch end
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step(); sched.step(); opt.zero_grad()
        vl = predict_logits(model, va, device)
        m = metrics(softmax(vl), val_y)
        hist.append({"epoch": ep, "train_loss": round(tot / max(1, k + 1), 4), "val_e2e_macro_f1": m["e2e_macro_f1"],
                     "val_gate_macro_f1": m["gate_macro_f1"], "val_category_macro_f1": m["category_macro_f1"],
                     "sec": round(time.time() - t0, 1)})
        log(json.dumps(hist[-1]))
        if m["e2e_macro_f1"] > best:
            best, bad, best_logits = m["e2e_macro_f1"], 0, vl
            best_state = {k2: v.detach().cpu().clone() for k2, v in model.state_dict().items()}
        else:
            bad += 1
            if bad >= cfg["patience"]:
                break
    model.load_state_dict(best_state)
    model.to("cpu")
    if device.type == "mps":
        torch.mps.empty_cache()
    return model, tok, hist, best_logits


class HFPredictor:
    """Local inference for an exported 7-way model directory (config + safetensors + tokenizer + a4_meta.json)."""

    def __init__(self, path: Path, device: str = "cpu"):
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
        meta = json.loads((Path(path) / "a4_meta.json").read_text())
        self.T, self.max_len = float(meta["temperature"]), int(meta["max_len"])
        self.tok = AutoTokenizer.from_pretrained(path)
        self.model = AutoModelForSequenceClassification.from_pretrained(path, dtype=torch.float32).to(device).eval()
        self.device = torch.device(device)
        labels = [self.model.config.id2label[i] for i in range(self.model.config.num_labels)]
        if labels != LABELS7:
            raise RuntimeError(f"unexpected label order {labels}")

    def predict_proba(self, texts, bs=64):
        enc = Encoded(self.tok, list(texts), self.max_len)
        return softmax(predict_logits(self.model, enc, self.device, bs), self.T)
