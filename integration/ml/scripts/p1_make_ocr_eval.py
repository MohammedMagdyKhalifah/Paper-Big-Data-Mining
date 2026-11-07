"""Build the SYNTHETIC OCR evaluation set: phone-sized screenshots rendered by headless Chrome from HTML,
so the reference text is known exactly (it is the DOM text, in reading order).

Usage (from this ml/ dir):  PYTHONPATH=.. .venv/bin/python scripts/p1_make_ocr_eval.py
Writes data/ocr_eval/synthetic/{images/*.png|jpg, manifest.jsonl}. Real screenshots (if any) go in
data/ocr_eval/real/ with the same manifest format and are never mixed with synthetic ones in reports.

Content: real AURA review texts (A4 train split, PII-masked items skipped), hand-written generic error
messages, and hand-written mixed Arabic-English complaint chats; plus images with no text.
Variants: clean PNG (500x1000 CSS px @2x) and a degraded copy (downscaled 0.6, JPEG q=55, like a forwarded screenshot).
"""
import html
import json
import random
import re
import subprocess
import tempfile
from pathlib import Path

import pandas as pd
from PIL import Image

ML = Path(__file__).resolve().parents[1]
OUT = ML / "data/ocr_eval/synthetic"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
FONTS = ["SF Arabic", "Geeza Pro", "Arial"]
SEED = 31

ERRORS = [  # (app header or None, title, message lines) — generic error screens, hand-written
    ("أبشر", "حدث خطأ غير متوقع", ["عذراً، حدث خطأ أثناء معالجة طلبك.", "يرجى المحاولة لاحقاً.", "رمز الخطأ: 500"]),
    (None, "تعذر الاتصال بالخادم", ["تحقق من اتصالك بالإنترنت وحاول مرة أخرى"]),
    ("توكلنا", "انتهت صلاحية الجلسة", ["الرجاء تسجيل الدخول مرة أخرى"]),
    ("نفاذ", "رمز التحقق غير صحيح", ["تبقى لديك محاولتان قبل إيقاف الحساب مؤقتاً"]),
    (None, "الخدمة غير متاحة حالياً", ["نعمل على إصلاح المشكلة، شكراً لصبركم"]),
    (None, "فشلت عملية الدفع", ["لم يتم خصم أي مبلغ من حسابك.", "Transaction ID: TX-88213"]),
    (None, "Something went wrong", ["Please try again later. (Error 503)"]),
    ("صحتي", "تعذر حجز الموعد", ["لا توجد مواعيد متاحة في الوقت الحالي"]),
    (None, "Network Error", ["Request timed out. Check your connection."]),
    ("ناجز", "عذراً، لا يمكن إتمام الطلب", ["الخدمة متوقفة للصيانة من الساعة 12 حتى 4 فجراً"]),
    (None, "خطأ في تسجيل الدخول", ["اسم المستخدم أو كلمة المرور غير صحيحة"]),
    (None, "تم إيقاف التطبيق", ["توقف التطبيق بشكل غير متوقع. هل تريد إرسال تقرير؟"]),
]
CHATS = [  # hand-written complaint messages (mixed Arabic-English, system names, negation/past)
    ["السلام عليكم", "من أمس أحاول أسجل دخول في توكلنا والـ OTP ما يوصلني"],
    ["التطبيق يعلق عند صفحة الدفع", "وكل مرة يطلع لي Error ويرجعني للرئيسية"],
    ["كانت عندي مشكلة في الدخول على صحتي", "بس انحلت بعد التحديث، شكراً"],
    ["حاولت أجدد الإقامة من أبشر وانخصم المبلغ مرتين", "والطلب ما تم!"],
    ["the app keeps crashing after the last update", "ما أقدر أفتح أي صفحة"],
    ["نفاذ ما يرسل إشعار التحقق", "وناجز يطلب التحقق عن طريق نفاذ فما أقدر أدخل"],
]

CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{width:500px;height:1000px;font-family:'%(font)s';background:%(bg)s;color:%(fg)s;direction:rtl;overflow:hidden}
.bar{height:56px;background:%(bar)s;color:#fff;font-size:20px;display:flex;align-items:center;justify-content:center;font-weight:600}
.wrap{padding:28px 22px}
.card{background:%(card)s;border-radius:14px;padding:20px;margin-top:40px;box-shadow:0 2px 10px rgba(0,0,0,.15)}
h1{font-size:22px;margin-bottom:14px}
p{font-size:17px;line-height:1.7}
.btn{margin-top:22px;background:%(bar)s;color:#fff;border-radius:10px;padding:10px;text-align:center;font-size:17px}
.bub{background:%(bub)s;border-radius:16px;padding:12px 14px;margin:14px 0 0 40px;font-size:17px;line-height:1.6}
.stars{display:flex;gap:6px;margin:8px 0 12px}.stars i{width:16px;height:16px;background:#f5a623;clip-path:polygon(50% 0,61% 35%,98% 35%,68% 57%,79% 91%,50% 70%,21% 91%,32% 57%,2% 35%,39% 35%)}
.ltr{direction:ltr;text-align:left}
"""
THEMES = {"light": dict(bg="#f2f3f5", fg="#1b1b1f", bar="#0a7a55", card="#ffffff", bub="#dcf8c6"),
          "dark": dict(bg="#121214", fg="#ececf1", bar="#1f6f8b", card="#22232a", bub="#2a3d33")}


def _p(line):
    cls = ' class="ltr"' if re.fullmatch(r"[\x00-\x7F]+", line) else ""
    return f"<p{cls}>{html.escape(line)}</p>"


def page(kind, font, theme, header=None, title=None, lines=()):
    t = THEMES[theme]
    css = CSS
    for k_, v_ in dict(font=font, **t).items():
        css = css.replace(f"%({k_})s", v_)
    ref, body = [], []
    if header:
        body.append(f'<div class="bar">{html.escape(header)}</div>')
        ref.append(header)
    body.append('<div class="wrap">')
    if kind == "error_screen":
        h_cls = ' class="ltr"' if re.fullmatch(r"[\x00-\x7F]+", title) else ""
        body.append(f'<div class="card"><h1{h_cls}>{html.escape(title)}</h1>' + "".join(_p(l) for l in lines)
                    + f'<div class="btn">{"OK" if h_cls else "حسناً"}</div></div>')
        ref += [title, *lines, "OK" if h_cls else "حسناً"]
    elif kind == "review":
        body.append('<div class="card"><h1>تقييم التطبيق</h1><div class="stars">' + "<i></i>" * 2 + "</div>"
                    + _p(lines[0]) + "</div>")
        ref += ["تقييم التطبيق", lines[0]]
    elif kind == "chat":
        body += [f'<div class="bub">{html.escape(l)}</div>' for l in lines]
        ref += list(lines)
    elif kind == "no_text":
        body.append('<div class="card" style="height:300px;background:linear-gradient(135deg,#7ad,#d7a)"></div>'
                    '<div class="stars" style="margin-top:40px;justify-content:center">' + "<i></i>" * 5 + "</div>")
    body.append("</div>")
    return f"<!doctype html><html><head><meta charset='utf-8'><style>{css}</style></head><body>{''.join(body)}</body></html>", "\n".join(ref)


def render(doc, png_path):
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as f:
        f.write(doc)
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=2",
                    "--window-size=500,1000", f"--screenshot={png_path}", f"file://{f.name}"],
                   check=True, capture_output=True, timeout=60)
    Path(f.name).unlink()


def review_texts(n, rng):
    lab = pd.read_parquet(ML / "data/a4/labels_a4.parquet")
    d = lab[(lab.set == "a4_train") & lab.review.str.len().between(60, 220)
            & ~lab.review.str.contains(r"\[|[A-Za-z]{3,}|\n", regex=True)]
    picks = []
    for lab_, k in [("NO", 3), ("AUTH", 2), ("AVAIL", 2), ("PERF", 1), ("TRANS", 2), ("UX", 2)]:
        sub = d[d.label_final == lab_]
        picks += sub.sample(k, random_state=rng.randint(0, 10**6)).itertuples()
    return [(r.item_id, r.review.strip(), r.label_final) for r in picks[:n]]


def main():
    rng = random.Random(SEED)
    img = OUT / "images"
    img.mkdir(parents=True, exist_ok=True)
    items = []
    for i, (hdr, title, lines) in enumerate(ERRORS):
        items.append(dict(id=f"err{i:02d}", kind="error_screen", header=hdr, title=title, lines=lines, source="handwritten"))
    for i, lines in enumerate(CHATS):
        items.append(dict(id=f"chat{i:02d}", kind="chat", header="المحادثة", title=None, lines=lines, source="handwritten"))
    for item_id, text, lab in review_texts(12, rng):
        items.append(dict(id=f"rev_{item_id}", kind="review", header=None, title=None, lines=[text],
                          source=f"AURA review (A4 train, {item_id})", reference_label=lab))
    for i in range(2):
        items.append(dict(id=f"notext{i}", kind="no_text", header=None, title=None, lines=[], source="generated"))
    rows = []
    for k, it in enumerate(items):
        font, theme = FONTS[k % 3], ["light", "dark"][(k // 3) % 2]
        doc, ref = page(it["kind"], font, theme, it["header"], it["title"], it["lines"])
        png = img / f"{it['id']}.png"
        render(doc, png)
        jpg = img / f"{it['id']}_degraded.jpg"
        im = Image.open(png).convert("RGB")
        im.resize((int(im.width * 0.6), int(im.height * 0.6)), Image.LANCZOS).save(jpg, quality=55)
        base = {k2: v for k2, v in it.items() if k2 not in ("lines",)}
        for f, variant in [(png, "clean_png"), (jpg, "degraded_jpg")]:
            rows.append({**base, "file": str(f.relative_to(OUT)), "variant": variant, "font": font, "theme": theme,
                         "reference_text": ref, "synthetic": True, "renderer": "headless Chrome (HTML)"})
    with open(OUT / "manifest.jsonl", "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(len(rows), "images ->", OUT)


if __name__ == "__main__":
    main()
