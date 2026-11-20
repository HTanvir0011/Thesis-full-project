"""Development-pair diagnostics behind the site calibration (SAP_v5.md) at journal size (tools/figstyle.py).

python tools/fig_site_cal.py   -> results/figures/fig_sitecal_diag.pdf/.png, copied to paper/figures
Reads results/site_cal/dev_diagnostics.json (written by tools/szch_dev_diag.py on the 24 SZCH development pairs only).
"""
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import figstyle as fs  # noqa: E402

OUT, PAPER = ROOT / "results" / "figures", ROOT / "paper" / "figures"


def main():
    s = json.loads((ROOT / "results" / "site_cal" / "dev_diagnostics.json").read_text())
    fig, (a, b) = fs.figure("double", height_mm=62, ncols=2, gridspec_kw={"width_ratios": [1, 1.25]})
    for model, label, color in (("ours", "ours", "#0072B2"), ("reference", "reference model", "#D55E00")):
        rows = sorted((float(k.split("k=")[1]), v) for k, v in s["sweep"].items() if k.startswith(model + " "))
        ks = [k for k, _ in rows]
        a.plot(ks, [v["psnr_cal"] for _, v in rows], "-o", color=color, ms=3, label=f"{label}, whole image")
        a.plot(ks, [v["psnr_cal_bone"] for _, v in rows], "--s", color=color, ms=3, label=f"{label}, bone region")
    a.axvline(1.0, color="0.5", lw=0.6, ls=":")
    a.set(xlabel="gain $k$ of the subtracted bone estimate", ylabel="PSNR$_{cal}$ (dB)")
    a.text(1.04, a.get_ylim()[1] - 0.2, "as trained", fontsize=8, color="0.35", va="top")
    a.legend(loc="lower left", fontsize=8, handlelength=1.6, borderaxespad=0.1)
    fs.panel_label(a, "a")

    e, loo, ceil = s["error_split"]["ours"], s["loo_smooth_correction"]["ours"], s["resolution_ceiling_512"]
    bars = [("ours as is", s["sweep"]["ours k=1.0"]["psnr_cal"], "#9ecae1"),
            ("ours, leave-one-out\nsite correction", loo["psnr_cal"], "#0072B2"),
            ("ours if all error broader\nthan 64 px were removed", e["psnr_cal_if_fixed_gt64"], "0.7"),
            ("ours if all error broader\nthan 16 px were removed", e["psnr_cal_if_fixed_gt16"], "0.55"),
            ("exact dual-energy bone\nat 512 px (oracle)", ceil["psnr_cal"], "0.35")]
    ys = list(range(len(bars)))[::-1]
    b.barh(ys, [v for _, v, _ in bars], color=[c for _, _, c in bars], height=0.62)
    for y, (_, v, _) in zip(ys, bars):
        b.text(v + 0.4, y, f"{v:.1f}", va="center", fontsize=8)
    b.set(yticks=ys, yticklabels=[t for t, _, _ in bars], xlim=(20, 46), xlabel="whole-image PSNR$_{cal}$ (dB)")
    fs.panel_label(b, "b")
    OUT.mkdir(parents=True, exist_ok=True)
    fs.save(fig, str(OUT / "fig_sitecal_diag"))
    for ext in (".pdf", ".png"):
        shutil.copyfile(OUT / f"fig_sitecal_diag{ext}", PAPER / f"fig_sitecal_diag{ext}")


if __name__ == "__main__":
    main()
