"""Package a manuscript as one Overleaf project: copy every table and figure that its sections reference from the generated outputs
(paper/tables, paper/figures, results/figures), then zip the LaTeX sources, tables/, figures/ and the text files.
python tools/pack_overleaf.py                 -> overleaf_submission.zip (Elsevier version, submission/) in the repository root
python tools/pack_overleaf.py --ieee          -> overleaf_ieee.zip (IEEE version, submission_ieee/)
--out <file.zip> writes elsewhere. Refuses if a referenced file is missing."""
import argparse
import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {"tables": [ROOT / "paper/tables"], "figures": [ROOT / "paper/figures", ROOT / "results/figures"]}


def pack(proj, tex_files, extra, out, tables, strip_comments=False):
    """tables(tex) -> referenced table paths ('tables/name.tex'); extra: [(file, name in the zip)].
    strip_comments: drop the '%' provenance lines of copied tables (they name internal scripts and plans)."""
    tex = "\n".join(p.read_text(encoding="utf-8") for p in tex_files)
    tex = "\n".join(re.sub(r"(?<!\\)%.*$", "", line) for line in tex.splitlines())
    wanted = sorted(set(tables(tex)) | set(re.findall(r"\{(figures/[^}]+)\}", tex)))
    missing = []
    for rel in wanted:
        kind, name = rel.split("/", 1)
        src = next((d / name for d in SOURCES[kind] if (d / name).is_file()), None)
        if src is None:
            missing.append(rel)
            continue
        (proj / kind).mkdir(exist_ok=True)
        if strip_comments and kind == "tables":
            lines = src.read_text(encoding="utf-8").splitlines()
            (proj / rel).write_text("\n".join(l for l in lines if not l.lstrip().startswith("%")) + "\n", encoding="utf-8", newline="\n")
        else:
            (proj / rel).write_bytes(src.read_bytes())
    assert not missing, f"referenced but not found: {missing}"
    files = [(f, f.relative_to(proj).as_posix()) for f in [*tex_files, *(proj / rel for rel in wanted)]] + extra
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for f, arc in files:
            z.write(f, arc)
    print(f"{out.name}: {len(files)} files, {out.stat().st_size / 1e6:.1f} MB ({len(wanted)} tables and figures copied)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--ieee", action="store_true", help="the IEEE two-column version (submission_ieee/)")
    ap.add_argument("--proj", default=None, help="another IEEE-style project folder, e.g. submission_tmi (main.tex, optional supplementary.tex)")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    sub = ROOT / "submission"
    if a.ieee or a.proj:
        proj = ROOT / (a.proj or "submission_ieee")
        tex = [proj / "main.tex", *([proj / "supplementary.tex"] if (proj / "supplementary.tex").exists() else []),
               *sorted((proj / "sections").glob("*.tex"))]
        extra = [(f, f.relative_to(proj).as_posix()) for f in (proj / "README.txt", proj / "vancouver-doi.bst", proj / "tools" / "freeze_refs.py")
                 if f.exists()]
        extra.append((sub / "refs.bib", "refs.bib"))
        pack(proj, tex, extra, Path(a.out or ROOT / f"overleaf_{proj.name}.zip"),
             lambda t: [f"tables/{n}.tex" for n in re.findall(r"\\restable(?:\[[^\]]*\])?\{([^}]+)\}", t)], strip_comments=bool(a.proj))
    else:
        tex = [sub / "main.tex", sub / "supplementary.tex", *sorted((sub / "sections").glob("*.tex"))]
        extra = [(f, f.name) for f in (sub / "refs.bib", sub / "highlights.txt", sub / "README.txt")]
        pack(sub, tex, extra, Path(a.out or ROOT / "overleaf_submission.zip"),
             lambda t: re.findall(r"\\(?:fittable|input)\{(tables/[^}]+)\}", t))
