"""Write protocol/freeze_v5.json once, after the SAP_v5 coefficients are fitted and before any held-out or audit step (SAP_v5.md).

usage: python tools/freeze_v5.py
Records the SHA-256 of SAP_v5.md, the code it runs, the fitted coefficients and the audit lesion library, and the git commit. Only the
frozen files must be committed (other tracked files may carry unrelated local edits).
"""
import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from freeze_v2 import sha  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
FILES = ["protocol/SAP_v5.md", "s4/site_cal.py", "s4/eval_real.py", "s4/audit_real.py", "s4/eval_ribcxr.py", "s4/stats.py",
         "tools/szch_site_cal.py", "tools/szch_dev_diag.py", "tests/test_site_cal.py", "results/site_cal_coef.json"]
UNTRACKED = ["outputs/lesions_test.npz"]  # git-ignored; hashed so the audit provably uses the same lesion library

if __name__ == "__main__":
    out = ROOT / "protocol" / "freeze_v5.json"
    if out.exists():
        sys.exit("freeze_v5.json already exists; the freeze is written once (record any change in DEVIATIONS.md)")
    dirty = subprocess.run(["git", "status", "--porcelain", "--", *FILES], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    if dirty:
        sys.exit("frozen files are not committed; commit first so the hash identifies the code that runs:\n" + dirty)
    missing = [p for p in FILES + UNTRACKED if not (ROOT / p).exists()]
    if missing:
        sys.exit(f"missing: {missing}")
    rec = dict(created=time.strftime("%Y-%m-%dT%H:%M:%S"),
               git_commit=subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip(),
               files={p: sha(ROOT / p) for p in FILES + UNTRACKED},
               primary="H16: on the 51 held-out SZCH pairs the site correction fitted on the 24 development pairs raises the bone-region "
                       "PSNR_cal of ours; image bootstrap, 10,000 resamples; one-sided 95 % lower bound of the paired difference > 0")
    out.write_text(json.dumps(rec, indent=1))
    print(json.dumps(rec, indent=1))
