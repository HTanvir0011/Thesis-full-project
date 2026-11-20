"""Site-appearance calibration of a soft-tissue estimate (protocol/SAP_v5.md).

Dual-energy (DES) soft-tissue images of one site differ from a radiograph minus its bone image by a smooth appearance field that the
per-image gain/offset of the fidelity metric cannot absorb. This module learns that field from paired development images:
ridge regression of the 16-px-blurred difference (DES - est), sampled on a 64 x 64 grid, on position (up to quadratic terms), the local
intensity of the radiograph and the local bone estimate. One coefficient vector per method; applied unchanged to new images.
The correction only adds a smooth field (no detail finer than about 16 px at 1024 px), so it cannot restore an erased lesion.
"""
import cv2
import numpy as np

SIZE, G, SIGMA, LAM = 1024, 64, 16, 1e-3
FEATURES = ["1", "x", "y", "x^2", "y^2", "xy", "I", "I^2", "B", "I*y", "I*x"]
_YY, _XX = np.mgrid[0:G, 0:G] / (G - 1) - 0.5


def grid(z):
    """16-px Gaussian blur, area-sampled onto the 64 x 64 grid."""
    return cv2.resize(cv2.GaussianBlur(z.astype(np.float32), (0, 0), SIGMA), (G, G), interpolation=cv2.INTER_AREA)


def feats(x, est):
    """Features of one image from the radiograph x and the soft-tissue estimate est (bone estimate b = x - est); -> (G*G, 11)."""
    gx, gb = grid(x), grid(x - est)
    return np.stack([np.ones_like(gx), _XX, _YY, _XX * _XX, _YY * _YY, _XX * _YY, gx, gx * gx, gb, gx * _YY, gx * _XX], -1).reshape(-1, 11)


def fit(items, lam=LAM):
    """items: [(x, des, est)] at SIZE px. -> coefficient vector w (len 11), ridge penalty lam * number of grid samples."""
    A = np.concatenate([feats(x, est) for x, _, est in items]).astype(np.float64)
    t = np.concatenate([grid(des - est).ravel() for _, des, est in items]).astype(np.float64)
    return np.linalg.solve(A.T @ A + lam * len(A) * np.eye(A.shape[1]), A.T @ t)


def apply(x, est, w):
    """Corrected soft-tissue estimate: est plus the smooth field predicted from x and est."""
    corr = (feats(x, est) @ np.asarray(w, np.float64)).reshape(G, G).astype(np.float32)
    return est + cv2.resize(corr, (x.shape[1], x.shape[0]), interpolation=cv2.INTER_CUBIC)


def base_soft(spec, device):
    """Soft-tissue estimator of a frozen method spec: identity | qure:<weights.ts> | ens:<ckpt>+<ckpt>..."""
    from .eval_real import make_ens, make_qure
    kind, _, arg = spec.partition(":")
    return {"identity": lambda: (lambda x: x), "qure": lambda: make_qure(arg, device), "ens": lambda: make_ens(arg, device)}[kind]()


def make_soft(arg, device):
    """arg = <coef.json>#<name>: the frozen correction of SAP_v5.md applied to that method's soft-tissue estimate."""
    import json
    path, _, name = arg.partition("#")
    c = json.load(open(path))["methods"][name]
    f = base_soft(c["spec"], device)
    return lambda x: apply(x, f(x), c["w"])


def leave_one_out(items, lam=LAM):
    """For each image: fit on the others, apply to it. -> list of corrected estimates (development estimate of the gain)."""
    return [apply(x, est, fit(items[:i] + items[i + 1:], lam)) for i, (x, _, est) in enumerate(items)]
