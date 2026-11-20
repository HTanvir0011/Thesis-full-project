"""Development-only PSNR diagnostics on the 24 SZCH development pairs (the 51 held-out pairs are never read).

Uses the evaluation protocol of s4/eval_real.py (1024 px, per-image gain/offset calibration, bone region = top 10 % of calibrated CXR - DES):
  1. bone-gain sweep: soft = x - k * bone_hat; calibrated PSNR (whole image, bone region, non-bone) and the removed-bone slope.
     The absorption A of an inserted lesion scales with k too, so any k != 1 has to be re-audited before use.
  2. error split of the model as used (k = 1): squared error inside / outside the bone region, in low / high spatial frequencies,
     and the share explained by residual DES bone signal.
  3. resolution ceiling: an oracle that knows the DES bone signal exactly but only at 512 px (area down, bicubic up, as our pipeline does).
  4. leave-one-image-out site-appearance correction (s4/site_cal.py), applied to every method: the development estimate behind SAP_v5.md.
Descriptive, development data only; no test, no decision rule.

python tools/szch_dev_diag.py --out outputs/psnr_diag
"""
import argparse
import json
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from s4.eval_real import SIZE, _psnr, calibrate, load_pairs, make_ens, make_qure  # noqa: E402
from s4.site_cal import leave_one_out  # noqa: E402

KS = [0.0, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 2.5, 3.0]


def region(x, gt):
    d = calibrate(x, gt) - gt  # DES bone signal in calibrated units
    return d, d > np.quantile(d, 0.90)


def light_metrics(x, gt, est):
    cal = calibrate(np.clip(est, 0, 1).astype(np.float32), gt)
    d, bone = region(x, gt)
    rem = cv2.GaussianBlur(calibrate(x, gt) - cal, (0, 0), 2).ravel()
    ds = cv2.GaussianBlur(d, (0, 0), 2).ravel()
    ds, rem = ds - ds.mean(), rem - rem.mean()
    return {"psnr_cal": _psnr(cal, gt)[0], "psnr_cal_bone": _psnr(cal, gt, bone)[0], "psnr_cal_nonbone": _psnr(cal, gt, ~bone)[0],
            "bone_slope_s2": float((ds * rem).sum() / max((ds * ds).sum(), 1e-12))}


def error_split(x, gt, est, sigma=4.0):
    cal = calibrate(np.clip(est, 0, 1).astype(np.float32), gt)
    e = cal - gt
    d, bone = region(x, gt)
    low = cv2.GaussianBlur(e, (0, 0), sigma)
    tot = float((e ** 2).sum())
    dc = d - d.mean()
    beta = float(((e - e.mean()) * dc).sum() / max((dc * dc).sum(), 1e-12))  # e ~ beta * d: residual bone signal
    r = {"share_err_bone_region": float((e[bone] ** 2).sum()) / tot,  # the bone region is 10 % of the pixels
         "share_err_low_freq": float((low ** 2).sum()) / tot, "share_err_high_freq": float(((e - low) ** 2).sum()) / tot,
         "residual_bone_beta": beta, "share_err_residual_bone": beta ** 2 * float((dc * dc).sum()) / tot}
    # scale bands of the error at 1024 px: fine texture (<4 px), rib scale (4-16, 16-64 px), broad background (>64 px)
    bl = {s: cv2.GaussianBlur(e, (0, 0), s) for s in (4, 16, 64)}
    for name, band in (("lt4", e - bl[4]), ("4to16", bl[4] - bl[16]), ("16to64", bl[16] - bl[64]), ("gt64", bl[64])):
        r[f"share_err_band_{name}"] = float((band ** 2).sum()) / tot
    for s in (16, 64):  # oracle: what PSNR would be if every error component broader than s px were removed
        r[f"psnr_cal_if_fixed_gt{s}"] = _psnr(np.clip(cal - bl[s], 0, 1), gt)[0]
    return r


def resolution_ceiling(x, gt, px=512):
    xc = calibrate(x, gt)
    d = xc - gt
    d_lo = cv2.resize(cv2.resize(d, (px, px), interpolation=cv2.INTER_AREA), (SIZE, SIZE), interpolation=cv2.INTER_CUBIC)
    return light_metrics(x, gt, xc - d_lo)


def loo_smooth_correction(items):
    """Leave-one-image-out site-appearance correction (s4/site_cal.py, tested in tests/test_site_cal.py) scored with the unchanged
    protocol. items: list of (x, gt, est). Returns the per-image metrics after correction."""
    return [light_metrics(x, gt, e) for (x, gt, _), e in zip(items, leave_one_out(items))]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="data/szch")
    ap.add_argument("--freeze", default="protocol/freeze_v2.json")
    ap.add_argument("--out", required=True)
    ap.add_argument("--device", default="cuda")
    a = ap.parse_args()
    fz = json.loads(Path(a.freeze).read_text())
    dev = set(fz["szch_dev"])
    assert len(dev) == 24 and not dev & set(fz["szch_heldout"]), "development list must be the 24 frozen development images"
    pairs = [p for p in load_pairs(a.root) if p[0] in dev]
    assert len(pairs) == 24, len(pairs)

    ours = make_ens("+".join(m["file"] for m in fz["models"]["ours"]), a.device)
    qw = fz["models"]["qure"][0]["file"]
    try:
        ref = make_qure(qw, a.device)
        ref(pairs[0][1])
    except RuntimeError as err:  # 4 GB laptop GPU: SwinV2-B at 1024 px may not fit
        print("reference model on CPU:", str(err).splitlines()[0])
        ref = make_qure(qw, "cpu")
    models = {"ours": ours, "reference": ref}

    rows, splits, ceil = [], [], []
    keep = {"identity": [], **{name: [] for name in models}}  # (x, gt, est at k = 1) for the leave-one-out correction
    for n, x, gt in pairs:
        ceil.append(dict(image=n, **resolution_ceiling(x, gt)))
        rows.append(dict(image=n, model="identity", k=0.0, **light_metrics(x, gt, x)))
        keep["identity"].append((x, gt, x))
        for name, f in models.items():
            b = x - f(x)  # bone estimate on the 1024 px grid
            for k in KS:
                rows.append(dict(image=n, model=name, k=k, **light_metrics(x, gt, x - k * b)))
            splits.append(dict(image=n, model=name, **error_split(x, gt, x - b)))
            keep[name].append((x, gt, x - b))
        splits.append(dict(image=n, model="identity", **error_split(x, gt, x)))
    loo = {name: loo_smooth_correction(items) for name, items in keep.items()}

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    for fn, rs in (("sweep.csv", rows), ("error_split.csv", splits), ("resolution_ceiling.csv", ceil)):
        keys = list(rs[0])
        (out / fn).write_text("\n".join([",".join(keys)] + [",".join(str(r[c]) for c in keys) for r in rs]))

    mean = lambda rs, c: float(np.mean([r[c] for r in rs]))  # noqa: E731
    summ = {"n_images": len(pairs), "sweep": {}, "best_k_per_image": {}, "error_split": {}, "resolution_ceiling_512": {}}
    for name in ["identity", *models]:
        for k in sorted({r["k"] for r in rows if r["model"] == name}):
            rs = [r for r in rows if r["model"] == name and r["k"] == k]
            summ["sweep"][f"{name} k={k}"] = {c: round(mean(rs, c), 3) for c in ("psnr_cal", "psnr_cal_bone", "psnr_cal_nonbone", "bone_slope_s2")}
        ss = [r for r in splits if r["model"] == name]
        summ["error_split"][name] = {c: round(mean(ss, c), 3) for c in ss[0] if c not in ("image", "model")}
    for name in models:
        for c in ("psnr_cal", "psnr_cal_bone"):
            best = [max((r for r in rows if r["model"] == name and r["image"] == n), key=lambda r: r[c])["k"] for n, _, _ in pairs]
            summ["best_k_per_image"][f"{name} {c}"] = {"median": float(np.median(best)), "min": min(best), "max": max(best)}
    summ["resolution_ceiling_512"] = {c: round(mean(ceil, c), 3) for c in ("psnr_cal", "psnr_cal_bone", "psnr_cal_nonbone")}
    summ["loo_smooth_correction"] = {name: {c: round(mean(rs, c), 3) for c in ("psnr_cal", "psnr_cal_bone", "psnr_cal_nonbone")}
                                     for name, rs in loo.items()}
    (out / "summary.json").write_text(json.dumps(summ, indent=1))
    print(json.dumps(summ, indent=1))


if __name__ == "__main__":
    main()
