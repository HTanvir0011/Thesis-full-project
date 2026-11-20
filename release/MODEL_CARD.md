---
license: cc-by-nc-sa-4.0
library_name: pytorch
pipeline_tag: image-to-image
tags:
  - medical-imaging
  - chest-x-ray
  - bone-suppression
datasets:
  - qureaiorg/ct2xr-projections
---

# Bone suppression for chest radiographs with a lesion-invariance regulariser (K = 3 ensemble)

**Research use only. Not a medical device. Not for diagnosis or any clinical decision.**

## Model description

The model predicts the **bone image** `b` of a frontal chest radiograph `x`; the bone-suppressed (soft-tissue) image is `x - b`. It is a deep
ensemble of **K = 3** members whose bone predictions are averaged.

| item | value |
|---|---|
| files | `twin16_cnx2_s0.pt`, `twin16_cnx2_s1.pt`, `twin16_cnx2_s2.pt` (seeds 0, 1, 2), 61.5 MB each, in release [v1.0.0](https://github.com/HTanvir0011/Thesis-full-project/releases/tag/v1.0.0) with `SHA256SUMS.txt` |
| checksums | identical to the hashes recorded before the evaluation (`protocol/freeze_v2.json`, entry `models.ours`) |
| encoder | ConvNeXt-V2-Tiny (`timm` `convnextv2_tiny.fcmae_ft_in22k_in1k`: FCMAE pre-training, ImageNet-22k then ImageNet-1k fine-tuning), 512 x 512 input |
| decoder | nested (UNet++) over the four encoder stages, CBAM attention, plain U-Net tail with two shallow convolutional skips, 1 x 1 head |
| parameters | 30.7 M per member (30,707,726) |
| output | bone image on the scale of the min-max normalised input |
| training | 300,000 samples per member (37,500 steps, batch 8), AdamW, learning rate 2e-4 (encoder 0.25 x); the checkpoints hold the EMA weights |
| regulariser | twin lesion-invariance regulariser, weight 16: each training image is paired with a copy that has a lesion pasted in while the bone target stays the same, and the two bone predictions are tied on the lesion support |
| paper | Hossin et al., *Lesion-Faithful Bone Suppression from Chest CT Projections: Counterfactual Auditing and Gains for Focal Lesion Detection and Classification in Chest Radiographs* (manuscript; the reference is added here on publication) |
| code | <https://github.com/HTanvir0011/Thesis-full-project> (package `s4`, MIT licence) |

Input convention (`s4/infer.py`): a frontal radiograph in standard display polarity (bone bright; invert MONOCHROME1 images first),
area-resized to 512 x 512 and min-max normalised to [0, 1] per image, as in training.

## Intended use and out-of-scope use

**Intended use.** Research on bone suppression in chest radiographs: reproducing the paper, comparing bone suppressors, studying how suppressors treat
lesions (the paper's counterfactual lesion audit), and teaching.

**Out of scope.**
- Any clinical use: diagnosis, triage, screening, treatment decisions, or showing the output to patients or to readers as a diagnostic image.
- Use as a replacement for dual-energy subtraction.
- Commercial use (the licence is non-commercial).
- Inputs outside the training distribution: lateral, portable or supine radiographs and non-chest images have not been evaluated; paediatric images only in a limited external validation.
- Re-identification of anyone, or linking outputs to personal data.

## Training data and licences

| source | use | licence |
|---|---|---|
| Qure.ai `ct2xr-projections` (public CT projections with bone, soft-tissue and lung components, built from CT-RATE volumes) | training images and exact bone targets | CC BY-NC-SA 4.0 |
| LIDC-IDRI (TCIA) | lesion patches pasted by the twin regulariser (library built from training CTs only) | CC BY 3.0 (attribution with the data DOI 10.7937/K9/TCIA.2015.LO9QL9SX) |
| ConvNeXt V2 Tiny pre-trained weights (`timm/convnextv2_tiny.fcmae_ft_in22k_in1k`) | encoder initialisation | CC BY-NC 4.0 (model page, read 2026-11-03) |

The weights were trained on CC BY-NC-SA 4.0 data from a CC BY-NC 4.0 initialisation and are released under **CC BY-NC-SA 4.0**: attribution,
non-commercial use, and share-alike for adaptations. Please credit Qure.ai and the CT-RATE and LIDC-IDRI providers, cite their papers (see
Citation), and follow the terms of their dataset cards.

No real radiograph and no real dual-energy pair is used as a training image: the released members are trained on the Qure.ai projections
alone, with a random gamma tone curve (the histogram matching to real radiographs used for the earlier LIDC-IDRI renders is not active for
them). The projections were translated by Qure.ai towards the appearance of real radiographs; their paper describes that step. Evaluation data
(SZCH-X-Rays, VinDr-RibCXR, JSRT, Node21, TBX11K, VinBigData, NIH ChestX-ray14, BDCXR-3257) were used only for evaluation and are not
redistributed.

## Evaluation

All numbers are in the paper and in the generated tables of the code repository; none are repeated here, so that this card cannot drift from
the results.

| what | where (code repository) |
|---|---|
| fidelity on held-out SZCH-X-Rays pairs | `paper/tables/szch_heldout.tex`, `paper/tables/h2_noninferiority.tex` |
| lesion absorption on VinDr-RibCXR, dose-response over the twin weight, ablation | `paper/tables/audit_ribcxr.tex`, `audit_contrasts.tex`, `dose_response.tex`, `ablation_twin.tex` |
| rib benchmark, real-nodule contrast | `paper/tables/rib_benchmark.tex`, `nodule_cnr.tex` |
| downstream classification and detection | `paper/tables/downstream_cls.tex`, `downstream_det.tex` |
| reliability (ensemble spread, conformal coverage) | `paper/tables/reliability.tex` |
| encoders | `paper/tables/encoders.tex` |

## Limitations and biases

- Trained only on synthetic, CT-derived radiographs; no real dual-energy pairs were used for training. The bone image of a real radiograph is never observed.
- The source CT population is that of CT-RATE (see its documentation); its demographics and acquisition sites limit generalisation.
- Real-image fidelity was measured against dual-energy images from one hospital and one acquisition set-up.
- A bone suppressor can remove lesion signal together with bone. The paper measures this with a counterfactual audit (absorption `A`); the
  regulariser lowers it to about a third of that of a released CT-supervised model but does not remove it, and the audit is linear and additive,
  so it is not a measure of clinical detectability.
- The prediction is made at 512 x 512; fine detail is limited by that resolution.
- The ensemble spread is a flag, not a guarantee; conformal intervals are calibrated on synthetic data and coverage on real images was measured under shift.
- Trained on adult CT projections. Paediatric radiographs were examined only in an external validation (pneumonia classification and the lesion audit; no fidelity truth); lateral, portable and supine radiographs were not evaluated.

## How to use

Clone the code repository (for the package `s4`) and install `torch`, `timm`, `opencv-python-headless` and `numpy`.

```python
import hashlib
import urllib.request

import cv2
import numpy as np

from s4.infer import load_suppressor, prep512, suppress_batch, to_u8

URL = "https://github.com/HTanvir0011/Thesis-full-project/releases/download/v1.0.0/"
SHA256 = {"twin16_cnx2_s0.pt": "fe7f3035f03b92f1396bfabad9955cf7268229f12714f3e049d5855f1de96a5d",
          "twin16_cnx2_s1.pt": "4f92c4d70e781b78b6a210fae5c0b9797b5cb80c67ad588584560ca834faed86",
          "twin16_cnx2_s2.pt": "154a126879f2cfbe8ac6e3c8aaecd9b84b3bbd3afe3cde81282c7934852f7685"}
for name, sha in SHA256.items():
    urllib.request.urlretrieve(URL + name, name)
    assert hashlib.sha256(open(name, "rb").read()).hexdigest() == sha, f"checksum mismatch: {name}"
model = load_suppressor("+".join(SHA256), device="cuda")  # K = 3 ensemble (mean bone image); use device="cpu" without a GPU

gray = cv2.imread("chest_xray.png", cv2.IMREAD_UNCHANGED).astype(np.float32)
if gray.ndim == 3:
    gray = cv2.cvtColor(gray, cv2.COLOR_BGR2GRAY)
x = prep512(gray)                                  # area-resize to 512 x 512, min-max to [0, 1]
b = suppress_batch(model, x[None], "cuda")[0]      # predicted bone image, float32 [512, 512]
soft = x - b                                       # bone-suppressed image
cv2.imwrite("bone.png", to_u8(np.clip(b, 0, 1)[None], 512)[0])
cv2.imwrite("soft.png", to_u8(np.clip(soft, 0, 1)[None], 512)[0])
```

`load_suppressor` also accepts a single checkpoint. Outputs are at 512 x 512; resize them yourself if you need the original size.

## Citation

Cite the code and weights as given in `CITATION.cff` of the code repository; the reference of the paper is added here on publication.
Please also cite the data sources: Angaitkar et al., "Anatomy-Decomposed Chest Computed Tomography (CT) Projections as Scalable Supervision for
Bone Suppression in Chest Radiographs", arXiv:2609.24937 (2026); Hamamci et al., "Generalist foundation models from a multimodal dataset for 3D
computed tomography", Nature Biomedical Engineering 10(8):1610-1628 (2026); Armato et al., Medical Physics 38(2):915-931 (2011),
doi:10.1118/1.3528204.
