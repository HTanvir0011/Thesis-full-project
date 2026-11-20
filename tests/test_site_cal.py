import cv2
import numpy as np

from s4 import site_cal


def _images(n, field, seed=0):
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(n):
        des = cv2.GaussianBlur(rng.random((256, 256), np.float32), (0, 0), 8) * 0.5 + 0.25
        out.append((des, des, des - field))  # radiograph = DES; the estimate misses a smooth field
    return out


def test_learned_field_is_removed_from_a_new_image():
    yy = np.mgrid[0:256, 0:256][0].astype(np.float32) / 255 - 0.5
    field = 0.1 * yy  # smooth top-to-bottom appearance difference
    train, (x, des, est) = _images(4, field), _images(1, field, seed=1)[0]
    w = site_cal.fit(train)
    before = np.abs(est - des).mean()
    after = np.abs(site_cal.apply(x, est, w) - des)[16:-16, 16:-16].mean()  # borders: blur edge effects
    assert after < 0.2 * before


def test_correction_is_smooth_so_a_small_lesion_passes_through():
    yy = np.mgrid[0:256, 0:256][0].astype(np.float32) / 255 - 0.5
    w = site_cal.fit(_images(4, 0.1 * yy))
    x = np.full((256, 256), 0.5, np.float32)
    lesion = np.zeros_like(x)
    lesion[120:126, 120:126] = 0.2  # 6 px, far below the 16 px smoothing scale
    d = site_cal.apply(x + lesion, x + lesion, w) - site_cal.apply(x, x, w)
    assert abs(float(d[120:126, 120:126].mean()) - 0.2) < 0.05  # the lesion keeps most of its amplitude in the corrected estimate
