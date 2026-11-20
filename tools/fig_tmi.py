"""Overview and architecture figures of the focused two-study paper (no CT-to-X-ray distillation) at journal size (tools/figstyle.py).

python tools/fig_tmi.py   -> results/figures/fig_tmi_workflow.pdf/.png and fig_tmi_architecture.pdf/.png, copied to paper/figures
Drawn from the methods as written (no data are read). The key results quoted in the overview come from the generated tables
(Study I: audit_contrasts, downstream_det; Study II: v3_primary, v3_groups, v3_pointing).
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from fig_framework import EDGE, arrow, box, canvas, save  # noqa: E402


def workflow(a):
    H = 72
    fig, ax = canvas(H)
    cols = [(8, 40, "Data"), (53, 44, "Models and training"), (102, 46, "Evaluation"), (153, 26, "Key result")]
    for x, w, t in cols:
        ax.text(x + w / 2, H - 4, t, ha="center", va="center", fontsize=9, fontweight="bold")
    rows = [
        ("I", H - 8 - 27, ["LIDC-IDRI renders (v1)\nQure.ai CT projections\n(exact bone and soft-tissue\ncomponents)",
                           "Bone suppressor: encoder +\nUNet++ decoder, twin lesion-\ninvariance loss, ensemble of 3,\nconformal intervals",
                           "Counterfactual lesion audit (A),\nfidelity on dual-energy pairs,\nrib benchmark, real nodules,\ndetection, classification",
                           "A = 0.051 vs\n0.149 (released)\nand 0.178 (control);\nNode21 CPM +0.028\nwith extra channels"]),
        ("II", H - 8 - 27 - 5 - 27, ["suppressor outputs $S$, $\\hat B$\nNIH ChestX-ray14,\nVinBigData, BDCXR-3257",
                                     "Multi-stream classifier,\n5 input configurations,\n5 seeds, 3 data sets\n(175 runs; 5 folds on\nBDCXR-3257)",
                                     "Macro-AUROC contrasts\n(capacity-matched control),\nfinding groups, pointing\ngame, conformal sets",
                                     "No overall gain\n(NIH +0.0001);\nfocal findings:\n+0.0089 AUROC,\nbetter pointing"])]
    for kind, y, texts in rows:
        h = 27
        ax.text(3.2, y + h / 2, f"Study {kind}", rotation=90, ha="center", va="center", fontsize=9, fontweight="bold", color=EDGE[kind])
        for (x, w, _), t in zip(cols, texts):
            box(ax, x, y, w, h, t, kind)
        for (x0, w0, _), (x1, _, _) in zip(cols, cols[1:]):
            arrow(ax, (x0 + w0, y + h / 2), (x1, y + h / 2))
    yg = H - 8 - 27 - 2.5  # elbow through the gap between the two studies
    ax.plot([75, 75, 28], [H - 8 - 27, yg, yg], color="0.25", lw=0.7)
    arrow(ax, (28, yg), (28, yg - 2.5))
    ax.text(51.5, yg + 0.4, "soft-tissue and bone images", ha="center", va="bottom", fontsize=8, style="italic", color="0.25")
    save(a, fig, "fig_tmi_workflow")


def architecture(a):
    dy = 63.0  # panels a and b of the three-study architecture figure, shifted up
    fig, ax = canvas(107)
    Y = lambda y: y - dy  # noqa: E731
    ax.text(1, Y(166), "a", fontsize=10, fontweight="bold", va="center")
    ax.text(5, Y(166), "Study I: bone suppressor with the twin lesion-invariance regulariser", fontsize=9, fontweight="bold", va="center")
    box(ax, 1, Y(145), 30, 14, "training image $x$\n(radiograph-like\ncomposite)", "I")
    box(ax, 1, Y(120), 30, 14, "twin $x^{+}$: lesion\nsignal $n$ pasted\nin the lung fields", "I")
    box(ax, 37, Y(120), 30, 39, "encoder\nConvNeXt-V2-T\nor SwinV2-T\n(512 px)\n\nshared weights", "white")
    box(ax, 73, Y(120), 30, 39, "UNet++ decoder\nwith CBAM,\nU-Net tail,\n1x1 head\n\nshared weights", "white")
    box(ax, 109, Y(145), 26, 14, "bone $\\hat b=f(x)$;\nsoft tissue\n$x-\\hat b$", "I")
    box(ax, 109, Y(120), 26, 14, "$f(x^{+})$; target\nstays $b$", "I")
    box(ax, 141, Y(120), 38, 39, "loss: $L_{sup}$ on $x$ and $x^{+}$\n$+\\;w\\,L_{inv}$\n\n$L_{inv}$: mean $|f(x^{+})-f(x)|$\non the lesion support $M$\n\n"
        "3-model ensemble:\nmean, spread and\nconformal intervals", "white")
    for y in (152, 127):
        arrow(ax, (31, Y(y)), (37, Y(y)))
        arrow(ax, (67, Y(y)), (73, Y(y)))
        arrow(ax, (103, Y(y)), (109, Y(y)))
        arrow(ax, (135, Y(y)), (141, Y(y)))
    ax.text(1, Y(112), "b", fontsize=10, fontweight="bold", va="center")
    ax.text(5, Y(112), "Study II: multi-stream classifier with a class-query decoder", fontsize=9, fontweight="bold", va="center")
    for t, y in (("radiograph $X$", 97), ("soft tissue $S$", 86), ("bone $\\hat B=X-S$", 75)):
        box(ax, 1, Y(y), 30, 8.5, t, "II")
        arrow(ax, (31, Y(y) + 4.25), (37, Y(y) + 4.25))
    box(ax, 37, Y(75), 30, 30.5, "shared encoder\nDenseNet-121\n(one weight set,\n256 px)", "white")
    box(ax, 73, Y(75), 30, 30.5, "$8\\times8$ tokens\nper stream\n+ stream embedding\n+ 2-D sine code", "white")
    box(ax, 109, Y(75), 30, 30.5, "class-query decoder\n2 layers, 8 heads,\none query per class", "white")
    box(ax, 145, Y(75), 34, 30.5, "linear head per class\n-> probabilities\n(NIH 14, VinBigData\n14, BDCXR-3257 3)", "white")
    for x in (67, 103, 139):
        arrow(ax, (x, Y(90.25)), (x + 6, Y(90.25)))
    ax.text(90, Y(69.5), "configurations: orig ($X$), soft ($S$), early ($X,S,\\hat B$ as channels), hybrid (three streams), "
            "ctrl ($X$ three times, same capacity)", ha="center", va="center", fontsize=8)
    save(a, fig, "fig_tmi_architecture")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    a = ap.parse_args([])
    a.out, a.paper = ROOT / "results" / "figures", ROOT / "paper" / "figures"
    a.out.mkdir(parents=True, exist_ok=True)
    workflow(a)
    architecture(a)
