"""SAP_v5.md: site-appearance calibration of the SZCH fidelity metric.

python tools/szch_site_cal.py fit                    # BEFORE the freeze: fit one coefficient vector per method on the 24 development pairs
python tools/szch_site_cal.py heldout                # AFTER the freeze: 51 held-out pairs, every method uncorrected and corrected (H16, H17)
python tools/szch_site_cal.py audit                  # AFTER the freeze: VinDr-RibCXR audit of ours and qure, uncorrected and corrected,
                                                     # in one run so all four share every site (licensed data: local only)
python tools/szch_site_cal.py audit_stats            # H18 from that run
python tools/szch_site_cal.py rib                    # descriptive D2: rib benchmark of the corrected ours and qure
"""
import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from s4 import site_cal  # noqa: E402
from s4.eval_real import load_pairs, metrics  # noqa: E402
from s4.stats import cluster_bootstrap_ci, non_inferior  # noqa: E402

FREEZE = ROOT / "protocol" / "freeze_v2.json"
COEF = ROOT / "results" / "site_cal_coef.json"
OUT = ROOT / "results" / "site_cal"
METHODS = ["identity", "ours", "notwin", "clia_v1", "qure"]  # SAP_v5.md; BS-LDM was trained on this site's DES pairs and is not corrected


def spec(name, fz):
    if name == "identity":
        return "identity"
    files = [m["file"] for m in fz["models"][name]]
    return f"qure:{files[0]}" if name == "qure" else "ens:" + "+".join(files)


def pairs_of(subset, fz):
    names = set(fz[subset])
    assert len(names) == {"szch_dev": 24, "szch_heldout": 51}[subset] and not set(fz["szch_dev"]) & set(fz["szch_heldout"])
    ps = [p for p in load_pairs(str(ROOT / "data" / "szch")) if p[0] in names]
    assert len(ps) == len(names), (len(ps), len(names))
    return ps


def fit(dev):
    fz = json.loads(FREEZE.read_text())
    if COEF.exists():
        sys.exit(f"{COEF} exists: the coefficients are fitted once, before the freeze (SAP_v5.md)")
    pairs = pairs_of("szch_dev", fz)
    rec = {"plan": "protocol/SAP_v5.md", "fitted_on": sorted(p[0] for p in pairs),
           "settings": dict(size=site_cal.SIZE, grid=site_cal.G, sigma=site_cal.SIGMA, lam=site_cal.LAM, features=site_cal.FEATURES),
           "methods": {}}
    for name in METHODS:
        s = spec(name, fz)
        f = site_cal.base_soft(s, dev)
        items = [(x, gt, f(x)) for _, x, gt in pairs]
        rec["methods"][name] = {"spec": s, "w": [float(v) for v in site_cal.fit(items)]}
        print(name, "fitted", flush=True)
    COEF.write_text(json.dumps(rec, indent=1))
    print("wrote", COEF)


def require_freeze():
    """The held-out pairs and the audit are read only after freeze_v5.json has recorded these exact coefficients (SAP_v5.md)."""
    import hashlib
    f5 = ROOT / "protocol" / "freeze_v5.json"
    if not f5.exists():
        sys.exit("protocol/freeze_v5.json is missing: freeze the plan before any held-out or audit step (SAP_v5.md)")
    rec = json.loads(f5.read_text())["files"]
    for p in ("results/site_cal_coef.json", "s4/site_cal.py", "tools/szch_site_cal.py"):
        if hashlib.sha256((ROOT / p).read_bytes()).hexdigest() != rec[p]:
            sys.exit(f"{p} changed after the freeze; record it in DEVIATIONS.md before running")


def heldout(dev):
    require_freeze()
    fz, coef = json.loads(FREEZE.read_text()), json.loads(COEF.read_text())
    pairs = pairs_of("szch_heldout", fz)
    rows = []
    for name, c in coef["methods"].items():
        f = site_cal.base_soft(c["spec"], dev)
        for n, x, gt in pairs:
            est = f(x)
            for corrected, e in ((False, est), (True, site_cal.apply(x, est, c["w"]))):
                rows.append(dict(method=name, corrected=corrected, image=n, **metrics(x, gt, e, dev)))
        print(name, "done", flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    keys = list(rows[0])
    (OUT / "heldout.csv").write_text("\n".join([",".join(keys)] + [",".join(str(r[k]) for k in keys) for r in rows]))

    def col(name, corrected, k):
        r = sorted((x for x in rows if x["method"] == name and x["corrected"] == corrected), key=lambda x: x["image"])
        return np.array([x[k] for x in r])

    res = {"n_images": len(pairs), "means": {}}
    for name in coef["methods"]:
        for corrected in (False, True):
            res["means"][f"{name}{'_cal' if corrected else ''}"] = {k: round(float(col(name, corrected, k).mean()), 4) for k in
                                                                   ("psnr_cal_bone", "psnr_cal", "ssim_cal", "psnr_raw", "lpips_cal")}
    for k in ("psnr_cal_bone", "psnr_cal"):  # H16 (bone region, primary) and H16b (whole image): gain of the correction for ours
        res[f"H16_{k}"] = non_inferior(col("ours", True, k) - col("ours", False, k), margin=0.0)
    res["H17_psnr_cal_bone"] = non_inferior(col("ours", True, "psnr_cal_bone") - col("qure", True, "psnr_cal_bone"), margin=0.5)
    (OUT / "heldout_stats.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


AUDIT_CSV = OUT / "audit_ribcxr.csv"


def audit(dev):
    require_freeze()
    import subprocess
    coef = json.loads(COEF.read_text())
    m = [coef["methods"]["ours"]["spec"], coef["methods"]["qure"]["spec"], f"sitecal:{COEF.relative_to(ROOT).as_posix()}#ours",
         f"sitecal:{COEF.relative_to(ROOT).as_posix()}#qure"]
    subprocess.run([sys.executable, "-m", "s4.audit_real", "--dataset", "ribcxr", "--root", "data/ribcxr_raw", "--lib", "outputs/lesions_test.npz",
                    "--device", dev, "--methods", *m, "--out", str(AUDIT_CSV)], cwd=ROOT, check=True)


def rib(dev):
    """Descriptive (SAP_v5.md D2): rib benchmark of the corrected models, beside results/final/rib/{ours,qure}.csv."""
    require_freeze()
    import subprocess
    for name in ("ours", "qure"):
        subprocess.run([sys.executable, "-m", "s4.eval_ribcxr", "--root", "data/ribcxr_raw", "--device", dev, "--method",
                        f"sitecal:{COEF.relative_to(ROOT).as_posix()}#{name}", "--out", str(OUT / f"rib_{name}_cal.csv")], cwd=ROOT, check=True)


def audit_stats():
    require_freeze()
    with open(AUDIT_CSV, newline="") as fh:
        rows = list(csv.DictReader(fh))
    A = {}
    for r in rows:  # labels: ens (ours), qure, ours_cal, qure_cal
        A.setdefault({"ens": "ours"}.get(r["method"], r["method"]), {})[(r["image"], int(r["site"]))] = float(r["absorption"])
    sites = sorted(A["ours"])
    assert all(sorted(v) == sites for v in A.values()), "every method must cover the same sites"
    a = {k: np.array([v[s] for s in sites]) for k, v in A.items()}
    img = [s[0] for s in sites]
    res = {"n_sites": len(sites), "mean_A": {k: round(float(v.mean()), 4) for k, v in a.items()}}
    final = ROOT / "results" / "final" / "audit_ribcxr"  # reproduction check of the uncorrected models (same code, sites drawn again)
    for k in ("ours", "qure"):
        with open(final / f"{k}.csv", newline="") as fh:
            res[f"final_mean_A_{k}"] = round(float(np.mean([float(r["absorption"]) for r in csv.DictReader(fh)])), 4)
    for lab, d in (("H18_ours_cal_minus_qure_cal", a["ours_cal"] - a["qure_cal"]), ("ours_cal_minus_ours", a["ours_cal"] - a["ours"]),
                   ("qure_cal_minus_qure", a["qure_cal"] - a["qure"])):
        m, lo, hi = cluster_bootstrap_ci(d, img)
        res[lab] = dict(mean=m, lo=lo, hi=hi)
    res["H18_pass"] = bool(res["H18_ours_cal_minus_qure_cal"]["hi"] < 0)
    (OUT / "audit_stats.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=["fit", "heldout", "audit", "audit_stats", "rib"])
    ap.add_argument("--device", default="cuda")
    a = ap.parse_args()
    {"fit": lambda: fit(a.device), "heldout": lambda: heldout(a.device), "audit": lambda: audit(a.device), "audit_stats": audit_stats,
     "rib": lambda: rib(a.device)}[a.step]()
