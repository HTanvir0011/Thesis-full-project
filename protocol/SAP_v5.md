# SAP_v5: site-appearance calibration of the SZCH fidelity metric (frozen 2026-11-17)

Status: **frozen 2026-11-17** by protocol/freeze_v5.json (approved by the author after the supervisor noted that our PSNR is lower than
other work). Written after the SAP_v2 results were known, so this is an exploratory addendum: it changes no earlier hypothesis, verdict,
table or figure. H2' (SAP_v2.md) stays as reported. Nothing below may change after the freeze except through DEVIATIONS.md.

## Background (development data only)
- H2' on the 51 held-out SZCH-X-Rays pairs: bone-region PSNR_cal 21.46 dB for ours, 21.51 for the reference model (Qure released weights);
  BS-LDM 28.57, trained on the 592 SZCH training pairs of the same hospital and scanner, which are not public.
- Diagnostics on the 24 development pairs (tools/szch_dev_diag.py, 2026-11-17; the held-out pairs were not read):
  - Subtracting more of the bone estimate lowers PSNR: whole-image PSNR_cal is best at half strength for every image (26.92 against
    25.66 dB at full strength), the bone region at about 0.75 (22.20 against 22.03). The reference model behaves the same way.
  - Resolution is not limiting: an oracle with the exact dual-energy bone signal, predicted at 512 px, reaches 41.7 dB.
  - Most error is broad: removing every error component broader than 64 px would give 29.2 dB (ours), and the raw radiograph shows the same
    broad error, so the dual-energy images differ from radiograph-minus-bone by a smooth appearance field that the per-image gain and
    offset of the metric cannot absorb.
  - Leave-one-image-out correction (below), development estimate: ours 25.66 -> 28.48 dB whole image and 22.03 -> 24.15 dB bone region;
    reference 25.76 -> 28.79 and 21.97 -> 24.47; identity 26.29 -> 27.55 and 20.33 -> 21.59.

## Correction (fixed; s4/site_cal.py; coefficients in results/site_cal_coef.json)
- Corrected estimate: est' = est + U(F w). F holds, on a 64 x 64 grid, the 16-px-blurred radiograph I and bone estimate B = x - est:
  [1, x, y, x^2, y^2, xy, I, I^2, B, I*y, I*x] (x, y: image position). w is the ridge solution (penalty 0.001 x number of grid samples)
  for the 16-px-blurred, grid-sampled difference DES - est, pooled over all 24 development pairs. U: bicubic upsampling to 1024 px.
- One w per method, fitted the same way on 2026-11-17 before this freeze: identity, ours (K = 3), no-twin control (K = 3), v1 model
  (clia, K = 3) and the reference model. BS-LDM was trained on this site's dual-energy images and is not corrected; it is reported as is.
- The fitted weight on B is about +0.35 for every CT-supervised model: the correction adds back about a third of the smoothed bone
  estimate, i.e. it weakens broad-scale suppression. D2 and H18 check what this does to rib suppression and lesion absorption.
- Unchanged: the frozen weights (freeze_v2.json), the evaluation protocol (s4/eval_real.py), the 51 held-out pairs, and the VinDr-RibCXR
  audit (s4/audit_real.py, outputs/lesions_test.npz, seed 7, six sites per image).

## Hypotheses
- **H16 (primary):** on the 51 held-out pairs the correction raises the bone-region PSNR_cal of ours. Paired mean difference
  (corrected - uncorrected), image bootstrap with 10,000 resamples; passes if the one-sided 95 % lower bound is above 0.
  H16b (secondary): the same for whole-image PSNR_cal.
- **H17 (secondary):** the corrected ours is non-inferior to the corrected reference model in bone-region PSNR_cal, margin 0.5 dB as in
  H2' (one-sided 95 % lower bound of the paired difference above -0.5 dB).
- **H18 (secondary, safety):** on VinDr-RibCXR (245 images, 1,470 sites; one run with ours, the reference model and both corrected, so all
  four share every site) the corrected ours absorbs less of an inserted lesion than the corrected reference model: paired site-level
  difference, image-cluster bootstrap with 10,000 resamples, two-sided 95 % upper bound below 0. The changes A(corrected) - A(uncorrected)
  of both models are reported with their intervals.
- H16 is the only confirmatory test; H16b, H17 and H18 are secondary, judged by their own bounds and reported without multiplicity
  correction.

## Descriptive
- D1: PSNR_cal (bone region and whole image), SSIM_cal, raw PSNR and LPIPS of every method, uncorrected and corrected, on the 51 held-out
  pairs; BS-LDM uncorrected from results/final/szch/bsldm.csv.
- D2: rib benchmark (s4/eval_ribcxr.py) of the corrected ours and reference model, beside their uncorrected results.
- D3: mean absorption of the uncorrected models in the H18 run beside results/final/audit_ribcxr (reproduction check).

## Reporting rules
- The correction is a site calibration learned from 24 paired images of the test hospital, not a property of the suppressor. Corrected
  numbers are always shown next to the uncorrected ones and labelled "site-calibrated (24 pairs)"; the abstract and H2' keep the
  uncorrected numbers.
- The 51 held-out pairs were already used for H2', so this test re-uses seen images; only the correction is new, and it was designed and
  fitted on the development pairs alone. Every result is reported whatever its direction, and a failed H16 is reported as failed.
- The coefficients derive from SZCH-X-Rays (CC BY-NC 4.0), so any release of them is non-commercial.

## Run (after the freeze)
    python tools/szch_site_cal.py heldout      # H16, H16b, H17, D1  -> results/site_cal/heldout*.{csv,json}
    python tools/szch_site_cal.py audit        # H18 run (licensed VinDr-RibCXR: local only, metrics only)
    python tools/szch_site_cal.py audit_stats  # H18, D3 -> results/site_cal/audit_stats.json
    python tools/szch_site_cal.py rib          # D2
The scripts stop unless freeze_v5.json records the current coefficient file and code. Compute (estimate, local RTX 3050): held-out about
15 min, audit about 1 h, rib benchmark about 20 min.
