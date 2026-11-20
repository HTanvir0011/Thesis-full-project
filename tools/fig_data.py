"""Data figures at journal size (tools/figstyle.py): the preprocessing pipeline of every image source (with real thumbnails where the licence
allows) and the split sizes of every data set.

python tools/fig_data.py   -> results/figures/fig_data_pipeline.pdf/.png and fig_data_splits.pdf/.png, copied to paper/figures
Facts come from submission/sections/data.tex and methods.tex. Thumbnails (nothing here is hand-picked: first in sorted order):
  real      LIDC-IDRI CT slice (CC BY 3.0), SZCH-X-Rays radiograph and dual-energy soft-tissue image (CC BY-NC 4.0; first development
            pair), one NIH ChestX-ray14 test radiograph (stored in the saved heat-map files).
  rendered  the Qure.ai and CT-RATE rows show a rendered LIDC-IDRI CT instead (composite X and exact bone B; lung, mediastinum and bone
            windows), marked with a dagger: no image derived from CT-RATE is shown anywhere in the manuscript.
  dummy     VinDr-RibCXR, JSRT, Node21, TBX11K, VinBigData and BDCXR-3257 (data use agreements or licences): deterministic variants of the
            same rendered LIDC-IDRI composite (contrast, noise, mirroring, framing), marked with a double dagger. A drawn chest icon is only
            the fallback when no CT is available.
Every text is wrapped to its box, and the script stops if any text still overflows.
"""
import glob
import re
import shutil
import sys
from pathlib import Path

import cv2
import numpy as np
from matplotlib.font_manager import FontProperties
from matplotlib.patches import Ellipse, FancyBboxPatch, Rectangle
from matplotlib.textpath import TextToPath

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT))
import figstyle as fs  # noqa: E402
from fig_framework import EDGE, arrow, canvas  # noqa: E402

OUT, PAPER = ROOT / "results" / "figures", ROOT / "paper" / "figures"
FS, LH = 8.0, 3.5  # text size (pt) and line height (mm)
CT_WINDOWS = {"lung": (-1350.0, 150.0), "med": (-160.0, 240.0), "bone": (-500.0, 1300.0)}  # s4/ct_prep.py WINDOWS (low, high HU)


# ---- thumbnails ------------------------------------------------------------------------------------------------------
def norm(a, lo=1, hi=99.5):
    a = np.asarray(a, np.float32)
    p0, p1 = np.percentile(a, [lo, hi])
    return np.clip((a - p0) / max(p1 - p0, 1e-9), 0, 1)


def small(a, px=192):
    return cv2.resize(np.ascontiguousarray(a, np.float32), (px, px), interpolation=cv2.INTER_AREA)


def lidc():
    """Rendered LIDC-IDRI test CT: slice, composite X, exact bone B and the CT-RATE windows (same code as the 'pipeline' figure of
    tools/generate_all_thesis_figures.py, so X and B equal its panels f and g). Cached in outputs/ (git-ignored)."""
    cache = ROOT / "outputs" / "fig_data_lidc.npz"
    if cache.exists():
        return dict(np.load(cache))
    import torch

    from s4 import compose as C
    from s4 import seg
    from s4.ct import load_series
    from s4.nodule import xml_series_uid
    from s4.render import render_ct
    ct = load_series(sorted(glob.glob(str(ROOT / "data/tcia_test/series/*.dcm"))))
    xmls = [p for p in glob.glob(str(ROOT / "data/lidc_xml/**/*.xml"), recursive=True) if xml_series_uid(p) == ct["meta"]["series_uid"]]
    arr, meta = render_ct(ct, xmls)
    hu = ct["hu"]
    body = seg.body_mask(hu)
    bone = seg.bone_mask(hu, ct["spacing"]) & body
    lung = seg.lung_mask(hu, body, bone)
    z = int(np.argmax(lung.sum((1, 2))))
    nod = np.zeros_like(arr["a_bone"])
    if meta["nodules"]:
        n0, p = meta["nodules"][0], arr["nod0"]
        nod[n0["y0"]:n0["y0"] + p.shape[0], n0["x0"]:n0["x0"] + p.shape[1]] = p
    a4 = torch.from_numpy(np.stack([arr["a_bone"], arr["a_nl"], arr["a_lung"], (nod > 0.02).astype(np.float32)]))[None].float()
    o = C.compose(a4, torch.tensor([C.KVPS.index(100)]), C.Physics("cpu"), gen=torch.Generator().manual_seed(0), detector=False)
    out = {"ct": np.clip((hu[z] + 1000) / 1400, 0, 1), "X": o["X"][0, 0].numpy(), "B": o["B"][0, 0].numpy()}
    out.update({f"win_{k}": np.clip((hu[z] - a) / (b - a), 0, 1) for k, (a, b) in CT_WINDOWS.items()})
    out = {k: v.astype(np.float32) for k, v in out.items()}
    cache.parent.mkdir(exist_ok=True)
    np.savez_compressed(cache, **out)
    return out


def dummy(x, flip=False, gamma=1.0, noise=0.0, crop=1.0, shrink=1.0):
    """Dummy radiograph: a deterministic variant of the rendered LIDC-IDRI composite x. It stands in for a data set whose images may not be
    shown and is not an image of that data set (the figure marks it with a double dagger)."""
    a = norm(x)
    if flip:
        a = np.ascontiguousarray(a[:, ::-1])
    n = a.shape[0]
    if crop < 1:  # tighter framing
        m = int(n * (1 - crop) / 2)
        a = cv2.resize(np.ascontiguousarray(a[m:n - m, m:n - m]), (n, n), interpolation=cv2.INTER_AREA)
    if shrink < 1:  # smaller chest in the frame
        k, frame = int(n * shrink), np.zeros((n, n), np.float32)
        o = (n - k) // 2
        frame[o:o + k, o:o + k] = cv2.resize(a, (k, k), interpolation=cv2.INTER_AREA)
        a = frame
    a = a ** gamma
    if noise:
        a = a + np.random.default_rng(7).normal(0, noise, a.shape).astype(np.float32)
    return norm(a, 0.5, 99.9)


def szch():
    """First SZCH-X-Rays development pair in sorted order: radiograph and dual-energy soft-tissue image."""
    from szch_split import is_dev
    p = Path(sorted(q for q in glob.glob(str(ROOT / "data/szch/CXR/*.png")) if is_dev(Path(q).stem))[0])
    rd = lambda f: cv2.imread(str(f), cv2.IMREAD_UNCHANGED).astype(np.float32)  # noqa: E731
    return rd(p), rd(p.parent.parent / "BS" / p.name)


def nih():
    """First NIH ChestX-ray14 test radiograph (sorted key) of the saved heat-map file of Study II; channel 0 is the radiograph."""
    z = np.load(ROOT / "results/v3/xai/nih_hyb_hybrid@densenet121_s0.maps.npz")
    return z[sorted(k for k in z.files if k.endswith("__x"))[0]][0]


def thumbs():
    t = {}
    for name, fn in (("lidc", lidc), ("szch", szch), ("nih", nih)):
        try:
            t[name] = fn()
        except Exception as e:  # a missing data set only costs its thumbnail: the row falls back to the icon
            print(f"thumbnail {name}: skipped ({type(e).__name__}: {e})")
    L = t.get("lidc")
    return {
        "lidc_ct": [small(L["ct"])] if L else None,
        "qure": [small(norm(L["X"])), small(norm(L["B"]))] if L else None,
        "ctrate": [small(L[f"win_{k}"]) for k in CT_WINDOWS] if L else None,
        "szch": [small(norm(a)) for a in t["szch"]] if "szch" in t else None,
        "nih": [small(norm(t["nih"]))] if "nih" in t else None,
        # dummies (double dagger): VinDr-RibCXR, JSRT | Node21, TBX11K | VinBigData | BDCXR-3257
        "vindr_jsrt": [small(dummy(L["X"], gamma=0.85)), small(dummy(L["X"], flip=True, gamma=1.25, noise=0.02))] if L else None,
        "node_tbx": [small(dummy(L["X"], crop=0.88)), small(dummy(L["X"], flip=True, crop=0.92, gamma=0.8))] if L else None,
        "vinbig": [small(dummy(L["X"], gamma=1.1, noise=0.03))] if L else None,
        "bdcxr": [small(dummy(L["X"], shrink=0.78, gamma=0.9))] if L else None,
    }


# ---- rows ------------------------------------------------------------------------------------------------------------
# (group, name, subtitle, thumbnail key (None: icon), preprocessing, split, badges); split = ("cells", header, [[train, val, test], ...])
# or ("merged", header, text); badges = [(study, text)]
ROWS = [
    ("CT-derived", "LIDC-IDRI CT", "1,018 series, 844 used", "lidc_ct",
     "bone, soft-tissue and lung masks; AP projection of each component, 512 × 512; physics at 80–130 kVp (training)",
     ("cells", "patient hash,\n70 / 10 / 20 %", [["588", "98", "158"]]), [("I", "v1 suppressors, lesion library")]),
    ("CT-derived", "Qure.ai projections", "21,887 projections †", "qure",
     "8-bit 512 × 512, X = T/255, exact bone image B; shared affine, lesion insertion, gamma, blur and noise on the composite",
     ("cells", "by patient\n(14,374 patients)", [["21,051", "406", "430"]]),
     [("I", "v2 suppressors"), ("III", "P0, P1 models\n20,533 / 396 / 415")]),
    ("CT-derived", "CT-RATE volumes", "2,156 volumes (subset) †", "ctrate",
     "24 axial slices over the lung extent; lung, mediastinum and bone windows as channels; body crop, 256 px",
     ("cells", "patient level, fixed seed", [["1,600", "259", "297"]]), [("III", "2.5D CT teacher")]),
    ("Paired, annotated", "SZCH-X-Rays", "75 paired DES images", "szch",
     "suppressor input at 512 px; lung masks (PSPNet, 1,024 px), exported once and shared by all models",
     ("cells", "hash of file name", [["–", "24 dev", "51 test"]]), [("I", "paired fidelity test"), ("I", "site calibration")]),
    ("Paired, annotated", "VinDr-RibCXR + JSRT", "245 + 247 images ‡", "vindr_jsrt",
     "suppressor input at 512 px; lung masks eroded by 49 px for audit sites; rib masks from radiologists (VinDr)",
     ("merged", "evaluation only, no training", "245 + 247 test images"), [("I", "locked lesion audit, rib benchmark")]),
    ("Downstream", "Node21, TBX11K", "Node21 (top), TBX11K (bottom) ‡", "node_tbx",
     "detector inputs at 512 px; Node21: two boxes under 4 px left out of the contrast analysis; TBX11K: official validation set is the test set",
     ("cells", "hash of image ID", [["3,440", "512", "930"], ["6,200", "688", "2,088"]]),
     [("I", "downstream detection; Node21 contrast")]),
    ("Downstream", "VinBigData", "14 findings ‡", "vinbig",
     "512 px (detection), 256 px (classification); findings kept when at least two readers marked them; augmentation as for NIH",
     ("cells", "hash of image ID", [["10,433", "1,469", "2,943"]]),
     [("I", "detection"), ("II", "classification"), ("III", "zero-shot transfer")]),
    ("Downstream", "NIH ChestX-ray14", "14 diseases", "nih",
     "256 × 256 px, per-image standardisation, learned affine map per stream; rotation ≤ 7°, scale 0.9–1.1, shift ≤ 3 %, brightness, contrast (shared by channels)",
     ("cells", "official test list, patient-level rest", [["77,890", "8,634", "25,596"]]),
     [("I", "downstream classification"), ("II", "classifier inputs"), ("III", "X-ray students")]),
    ("External", "BDCXR-3257", "paediatric, 3,257 images ‡", "bdcxr",
     "JPEG, classifier inputs as for NIH (256 px); 5 class-stratified folds, fold seed 0; 48 near-duplicate pairs grouped (r ≥ 0.93)",
     ("merged", "near-duplicate groups, 5 folds", "3,257 images, out-of-fold test"),
     [("I", "external validation (E1–E3)"), ("II", "third classifier dataset")]),
]

# ---- layout (mm on a 180 mm canvas) ---------------------------------------------------------------------------------------
SRC_X, SRC_W, PRE_X, PRE_W, SPL_X, SPL_W, BAD_X, BAD_W = 5.0, 41.0, 49.0, 55.0, 107.0, 32.0, 142.0, 37.0
THUMB_W, ROMAN_W, CELL_H, PAD = 17.0, 4.6, 5.0, 1.6
HEADER_H, ROW_GAP, GROUP_GAP = 16.0, 1.4, 3.6
_T2P = TextToPath()


def width_mm(s, bold=False):
    w, _, _ = _T2P.get_text_width_height_descent(s, FontProperties(size=FS, weight="bold" if bold else "normal"), False)
    return w / 72 * 25.4


def glue(text):
    """Non-breaking spaces inside numbers with units, products and comparisons, so a line never breaks inside '512 × 512', '256 px' or '≤ 7°'."""
    for pat, rep in ((r"(\d) (px|kVp|%)", "\\1\u00a0\\2"), (r"([≤≥]) (\d)", "\\1\u00a0\\2"), (r"(\d) × (\d)", "\\1\u00a0×\u00a0\\2"),
                     (r"\br ≥", "r\u00a0≥"), (r"(\d) / (\d)", "\\1\u00a0/\u00a0\\2")):
        text = re.sub(pat, rep, text)
    return text


def wrap(text, w, bold=False):
    out = []
    for para in glue(text).split("\n"):
        cur = ""
        for word in para.split(" "):
            assert width_mm(word, bold) <= w + 1e-6, f"word {word!r} is wider than its {w:.1f} mm box"
            t = f"{cur} {word}".strip()
            if cur and width_mm(t, bold) > w:
                out.append(cur)
                cur = word
            else:
                cur = t
        out.append(cur)
    return out


def plan(row):
    """Wrapped texts and the height of each column box of one row."""
    _, name, sub, _, pre, split, badges = row
    tw = SRC_W - 1.5 - THUMB_W - 1.5 - 1.0
    nl, sl, pl = wrap(name, tw, True), wrap(sub, tw), wrap(pre, PRE_W - 2.4)
    kind, header, body = split
    hl = wrap(header, SPL_W - 2.0)
    ml = wrap(body, SPL_W - 2.0) if kind == "merged" else None
    low = len(body) * CELL_H if kind == "cells" else len(ml) * LH + 1.8
    bl = [wrap(t, BAD_W - ROMAN_W - 2.2) for _, t in badges]
    bh = [max(len(x) * LH + 1.4, ROMAN_W) for x in bl]
    heights = [(len(nl) + len(sl)) * LH + 2 * PAD, len(pl) * LH + 2 * PAD, len(hl) * LH + low + 2.4, sum(bh) + 1.2 * (len(bh) - 1) + 1.0, 14.5]
    return dict(nl=nl, sl=sl, pl=pl, hl=hl, ml=ml, low=low, bl=bl, bh=bh, h=max(heights))


# ---- drawing -------------------------------------------------------------------------------------------------------------
def icon(ax, x, y, s):
    """Drawn chest icon (two lungs, spine) for the sets whose images may not be shown."""
    ax.add_patch(FancyBboxPatch((x, y), s, s, boxstyle="round,pad=0,rounding_size=1.2", fc="#F0F0F0", ec="0.6", lw=0.5, zorder=3))
    for sx in (-1, 1):
        ax.add_patch(Ellipse((x + s / 2 + sx * 0.22 * s, y + s * 0.47), 0.3 * s, 0.56 * s, fc="white", ec="0.45", lw=0.5, zorder=4))
    ax.plot([x + s / 2] * 2, [y + 0.18 * s, y + 0.82 * s], color="0.45", lw=0.5, zorder=4)
    ax.plot([x + 0.27 * s, x + 0.73 * s], [y + 0.84 * s] * 2, color="0.45", lw=0.5, zorder=4)  # clavicles


def thumb(ax, x, y, h, imgs):
    """Real or rendered images side by side, centred in the 17 mm thumbnail area, or the icon when there are none."""
    if not imgs:
        s = min(h, 13.0)
        return icon(ax, x + (THUMB_W - s) / 2, y + (h - s) / 2, s)
    n, gap = len(imgs), 0.6
    s = min(h, 14.0, (THUMB_W - gap * (n - 1)) / n)
    x0, y0 = x + (THUMB_W - (n * s + gap * (n - 1))) / 2, y + (h - s) / 2
    for i, im in enumerate(imgs):
        xi = x0 + i * (s + gap)
        ax.imshow(im, cmap="gray", vmin=0, vmax=1, extent=(xi, xi + s, y0, y0 + s), aspect="auto", interpolation="bilinear", zorder=3)
        ax.add_patch(Rectangle((xi, y0), s, s, fill=False, ec="0.25", lw=0.4, zorder=5))


def rows_for(tmi):
    """tmi: the focused two-study paper, without the CT-to-X-ray distillation (Study III): drop its badges and the rows only it uses."""
    if not tmi:
        return ROWS
    return [(g, n, s, k, p, sp, [b for b in bs if b[0] != "III"]) for g, n, s, k, p, sp, bs in ROWS if any(b[0] != "III" for b in bs)]


def pipeline(tmi=False):
    fs.apply()
    rows = rows_for(tmi)
    plans = [plan(r) for r in rows]
    groups = [r[0] for r in rows]
    H = HEADER_H + sum(p["h"] for p in plans) + ROW_GAP * (len(rows) - 1 - (len(set(groups)) - 1)) + GROUP_GAP * (len(set(groups)) - 1) + 1.0
    fig, ax = canvas(round(H, 1))
    th = thumbs()
    texts = []  # (text object, box (x0, y0, x1, y1)) for the overflow check

    def put(x, y, s, box, **kw):
        t = ax.text(x, y, s, fontsize=FS, linespacing=1.22, zorder=6, **kw)
        texts.append((t, box))
        return t

    # header: legend, column titles, train / val / test labels
    H = round(H, 1)
    for i, (k, lab) in enumerate((("I", "Study I"), ("II", "Study II"), ("III", "Study III"))[: 2 if tmi else 3]):
        ax.add_patch(Rectangle((SRC_X + 1 + i * 24, H - 4.4), 3.2, 3.2, fc=EDGE[k], ec="none"))
        ax.text(SRC_X + 5 + i * 24, H - 2.8, lab, fontsize=FS, va="center")
    for x, t in ((SRC_X, "RAW SOURCE"), (PRE_X, "PREPROCESSING"), (SPL_X, "SPLIT"), (BAD_X, "USED BY")):
        ax.text(x, H - 9.0, t, fontsize=FS, fontweight="bold", color="0.25", va="center")
    for j, t in enumerate(("train", "val", "test")):
        ax.text(SPL_X + SPL_W * (j + 0.5) / 3, H - 12.4, t, fontsize=FS, color="0.4", ha="center", va="center")
    ax.plot([2, 180], [H - 14.4, H - 14.4], color="0.4", lw=0.8)

    y = H - HEADER_H
    start = y
    prev = None
    spans = []  # (group, y_top, y_bottom)
    for row, p in zip(rows, plans):
        group, name, sub, key, pre, split, badges = row
        if prev is not None and group != prev[0]:
            spans.append((prev[0], prev[1], y + ROW_GAP))
            y -= GROUP_GAP - ROW_GAP
            ax.plot([2, 180], [y + (GROUP_GAP - ROW_GAP) / 2 + ROW_GAP] * 2, color="0.7", lw=0.5)
            prev = None
        if prev is None:
            prev = (group, y)
        h, yb = p["h"], y - p["h"]
        yc = yb + h / 2
        for x, w in ((SRC_X, SRC_W), (PRE_X, PRE_W), (SPL_X, SPL_W)):
            ax.add_patch(Rectangle((x, yb), w, h, fc="white", ec="0.2", lw=0.6, zorder=2))
        # source: thumbnail, bold name, grey subtitle
        thumb(ax, SRC_X + 1.5, yb + 1.2, h - 2.4, th.get(key) if key else None)
        tx, lines = SRC_X + 1.5 + THUMB_W + 1.5, len(p["nl"]) + len(p["sl"])
        top = yc + lines * LH / 2
        box = (SRC_X, yb, SRC_X + SRC_W, y)
        put(tx, top, "\n".join(p["nl"]), box, fontweight="bold", va="top", ha="left")
        put(tx, top - len(p["nl"]) * LH, "\n".join(p["sl"]), box, color="0.4", va="top", ha="left")
        # preprocessing
        put(PRE_X + 1.2, yc, "\n".join(p["pl"]), (PRE_X, yb, PRE_X + PRE_W, y), va="center", ha="left")
        # split
        kind, header, body = split
        low = p["low"]
        ax.plot([SPL_X, SPL_X + SPL_W], [yb + low] * 2, color="0.6", lw=0.4, zorder=3)
        put(SPL_X + SPL_W / 2, yb + low + (h - low) / 2, "\n".join(p["hl"]), (SPL_X, yb + low, SPL_X + SPL_W, y), color="0.4", va="center", ha="center")
        if kind == "cells":
            for r_i, cells in enumerate(body):
                yr = yb + low - (r_i + 1) * CELL_H
                if r_i:
                    ax.plot([SPL_X, SPL_X + SPL_W], [yr + CELL_H] * 2, color="0.6", lw=0.4, zorder=3)
                for j, c in enumerate(cells):
                    cx0 = SPL_X + SPL_W * j / 3
                    put(cx0 + SPL_W / 6, yr + CELL_H / 2, c, (cx0, yr, cx0 + SPL_W / 3, yr + CELL_H), va="center", ha="center")
            for j in (1, 2):
                ax.plot([SPL_X + SPL_W * j / 3] * 2, [yb, yb + low], color="0.6", lw=0.4, zorder=3)
        else:
            put(SPL_X + SPL_W / 2, yb + low / 2, "\n".join(p["ml"]), (SPL_X, yb, SPL_X + SPL_W, yb + low), va="center", ha="center")
        # badges, fanned out from the split box
        tot = sum(p["bh"]) + 1.2 * (len(p["bh"]) - 1)
        yt = yc + tot / 2
        for (study, _), lines_b, bh in zip(badges, p["bl"], p["bh"]):
            ybb = yt - bh
            ax.add_patch(Rectangle((BAD_X, ybb), BAD_W, bh, fc="white", ec=EDGE[study], lw=0.9, zorder=2))
            ax.add_patch(Rectangle((BAD_X, ybb), ROMAN_W, bh, fc=EDGE[study], ec=EDGE[study], lw=0.9, zorder=3))
            ax.text(BAD_X + ROMAN_W / 2, ybb + bh / 2, study, fontsize=FS, fontweight="bold", color="white", ha="center", va="center", zorder=6)
            put(BAD_X + ROMAN_W + 1.0, ybb + bh / 2, "\n".join(lines_b), (BAD_X + ROMAN_W, ybb, BAD_X + BAD_W, ybb + bh), va="center", ha="left")
            arrow(ax, (SPL_X + SPL_W, yc), (BAD_X, ybb + bh / 2), color=EDGE[study])
            yt = ybb - 1.2
        for x0, w0, x1 in ((SRC_X, SRC_W, PRE_X), (PRE_X, PRE_W, SPL_X)):
            arrow(ax, (x0 + w0, yc), (x1, yc))
        y = yb - ROW_GAP
    spans.append((prev[0], prev[1], y + ROW_GAP))
    for g, top, bottom in spans:  # group labels
        ax.text(2.4, (top + bottom) / 2, g, fontsize=FS, color="0.4", rotation=90, ha="center", va="center")
    ax.set(xlim=(0, 180), ylim=(0, H))
    fig.canvas.draw()
    inv, ren = ax.transData.inverted(), fig.canvas.get_renderer()
    bad = []
    for t, (x0, y0, x1, y1) in texts:
        bb = t.get_window_extent(ren).transformed(inv)
        if bb.x0 < x0 - 0.2 or bb.x1 > x1 + 0.2 or bb.y0 < y0 - 0.2 or bb.y1 > y1 + 0.2:
            bad.append((t.get_text()[:30], round(bb.x0 - x0, 2), round(x1 - bb.x1, 2), round(bb.y0 - y0, 2), round(y1 - bb.y1, 2)))
    assert not bad, f"text outside its box (text, margins left/right/bottom/top in mm): {bad}"
    return fig


# (data set, training, validation or development, test or held-out); None: not used for that part
SPLITS = [
    ("NIH ChestX-ray14", 77890, 8634, 25596), ("VinBigData", 10433, 1469, 2943), ("TBX11K", 6200, 688, 2088),
    ("Node21", 3440, 512, 930), ("Qure.ai projections", 21051, 406, 430), ("Study III projections", 20533, 396, 415),
    ("CT-RATE volumes", 1600, 259, 297), ("LIDC-IDRI CTs", 588, 98, 158), ("SZCH-X-Rays pairs", None, 24, 51),
    ("VinDr-RibCXR", None, None, 245), ("JSRT", None, None, 247), ("BDCXR-3257 (5 folds)", None, None, 3257),
]


def splits(tmi=False):
    data = [s for s in SPLITS if not (tmi and (s[0].startswith("Study III") or s[0].startswith("CT-RATE")))]
    fig, ax = fs.figure("single", aspect=0.95)
    style = [("training", "o", "#0072B2"), ("validation / development", "s", "#E69F00"), ("test / held-out", "^", "#009E73")]
    ys = list(range(len(data)))[::-1]
    for y, (name, *counts) in zip(ys, data):
        ax.axhline(y, color="0.92", lw=0.5, zorder=0)
        for (label, marker, color), n in zip(style, counts):
            if n is not None:
                cv = name.startswith("BDCXR")
                ax.scatter(n, y, marker="D" if cv else marker, s=16, color="#6A51A3" if cv else color, zorder=3,
                           label=None if cv else label)
    ax.set(xscale="log", xlim=(10, 2e5), ylim=(-0.7, len(data) - 0.3), yticks=ys, yticklabels=[s[0] for s in data],
           xlabel="images, CT volumes or pairs (log scale)")
    ax.scatter([], [], marker="D", s=16, color="#6A51A3", label="cross-validation (all)")
    handles, labels = ax.get_legend_handles_labels()
    keep = dict(zip(labels, handles))
    ax.legend(keep.values(), keep.keys(), loc="lower center", bbox_to_anchor=(0.35, 1.0), ncol=2, fontsize=8, handletextpad=0.3,
              columnspacing=0.8, borderaxespad=0.2)
    return fig


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for name, make in (("fig_data_pipeline", pipeline), ("fig_data_splits", splits),
                       ("fig_data_pipeline_tmi", lambda: pipeline(True)), ("fig_data_splits_tmi", lambda: splits(True))):
        fs.save(make(), str(OUT / name))
        for ext in (".pdf", ".png"):
            shutil.copyfile(OUT / f"{name}{ext}", PAPER / f"{name}{ext}")
