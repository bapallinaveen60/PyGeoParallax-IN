"""Alignment metrics between a satellite field and a radar field on the same grid.

All functions take 2-D arrays on a common grid and an optional ``valid`` mask
(e.g. inside radar range). NaNs are always excluded.
"""

from __future__ import annotations

import numpy as np


def _valid(a, b, valid):
    ok = np.isfinite(a) & np.isfinite(b)
    if valid is not None:
        ok &= np.asarray(valid, bool)
    return ok


def iou(a, b, valid=None):
    """Intersection over union of two boolean masks."""
    a = np.asarray(a, bool)
    b = np.asarray(b, bool)
    if valid is not None:
        a = a & valid
        b = b & valid
    union = np.count_nonzero(a | b)
    return np.nan if union == 0 else np.count_nonzero(a & b) / union


def pearson(a, b, valid=None):
    """Pearson correlation of two fields over their common valid cells."""
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    ok = _valid(a, b, valid)
    if ok.sum() < 3:
        return np.nan
    x = a[ok] - a[ok].mean()
    y = b[ok] - b[ok].mean()
    den = np.sqrt((x * x).sum() * (y * y).sum())
    return np.nan if den == 0 else float((x * y).sum() / den)


def mutual_information(a, b, bins=32, valid=None, normalized=False):
    """Mutual information [bits] from a joint histogram.

    With ``normalized=True``, returns MI / sqrt(H(a) H(b)), which is in [0, 1].
    """
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    ok = _valid(a, b, valid)
    if ok.sum() < 2:
        return np.nan
    joint, _, _ = np.histogram2d(a[ok], b[ok], bins=bins)
    pxy = joint / joint.sum()
    px = pxy.sum(axis=1, keepdims=True)
    py = pxy.sum(axis=0, keepdims=True)
    nz = pxy > 0
    mi = float((pxy[nz] * np.log2(pxy[nz] / (px @ py)[nz])).sum())
    if not normalized:
        return mi
    hx = -float((px[px > 0] * np.log2(px[px > 0])).sum())
    hy = -float((py[py > 0] * np.log2(py[py > 0])).sum())
    return np.nan if hx == 0 or hy == 0 else mi / np.sqrt(hx * hy)


def _shifted(a, dy, dx):
    """``a`` moved by (dy, dx) cells (positive = south / east), NaN-padded."""
    out = np.full(a.shape, np.nan)
    ny, nx = a.shape
    src = a[max(0, -dy):ny - max(0, dy), max(0, -dx):nx - max(0, dx)]
    out[max(0, dy):max(0, dy) + src.shape[0], max(0, dx):max(0, dx) + src.shape[1]] = src
    return out


def best_displacement(a, b, max_lag=5, valid=None):
    """The shift of ``a`` that best matches ``b``, by maximum correlation.

    Searches all integer shifts up to ``max_lag`` cells. The residual offset
    between satellite and radar should be near zero after parallax correction.

    Returns
    -------
    dy, dx, r : int, int, float
        Rows (positive = move ``a`` south) and columns (positive = move ``a``
        east), and the correlation at that shift.
    """
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    best = (0, 0, -np.inf)
    for dy in range(-max_lag, max_lag + 1):
        for dx in range(-max_lag, max_lag + 1):
            r = pearson(_shifted(a, dy, dx), b, valid)
            if np.isfinite(r) and r > best[2]:
                best = (dy, dx, r)
    return best


def subcell_displacement(a, b, max_lag=5, valid=None):
    """Like :func:`best_displacement`, refined to a fraction of a cell.

    A parabola is fitted through the correlation at the best integer shift and
    its two neighbours, separately along rows and columns. The vertex gives
    the fractional shift. This resolves offsets smaller than one grid cell,
    e.g. the 1-2 km left after parallax correction on a 2 km grid. At the edge
    of the search, or where the peak is flat, the integer shift is returned.

    Returns
    -------
    dy, dx, r : float, float, float
    """
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    dy, dx, r0 = best_displacement(a, b, max_lag, valid)

    def vertex(rm, rp):
        den = rm - 2 * r0 + rp
        if not (np.isfinite(rm) and np.isfinite(rp)) or den >= 0:
            return 0.0
        return float(np.clip(0.5 * (rm - rp) / den, -0.5, 0.5))

    fy = fx = 0.0
    if abs(dy) < max_lag:
        fy = vertex(pearson(_shifted(a, dy - 1, dx), b, valid), pearson(_shifted(a, dy + 1, dx), b, valid))
    if abs(dx) < max_lag:
        fx = vertex(pearson(_shifted(a, dy, dx - 1), b, valid), pearson(_shifted(a, dy, dx + 1), b, valid))
    return dy + fy, dx + fx, r0


def compare(sat, radar, sat_threshold, radar_threshold, sat_below=True, valid=None,
            max_lag=5, bins=32):
    """All alignment metrics for one satellite/radar pair.

    Parameters
    ----------
    sat, radar : ndarray
        E.g. brightness temperature [K] and reflectivity [dBZ] on the same grid.
    sat_threshold, radar_threshold : float
        Thresholds defining the satellite and radar features, e.g. 235 K cold
        cloud and 20 dBZ echo.
    sat_below : bool, optional
        True if the satellite feature lies below the threshold (cold cloud tops).
    valid : ndarray of bool, optional
        Cells to evaluate (e.g. within radar range).

    Returns
    -------
    dict
        ``iou``, ``pearson`` and ``mutual_info`` (normalized), plus ``lag_dy``,
        ``lag_dx`` (whole cells), ``lag_dy_sub`` / ``lag_dx_sub`` (sub-cell, from
        :func:`subcell_displacement`) and ``lag_r``. Pearson and lag
        use the negated satellite field when ``sat_below`` is True, so a good
        match is always a positive correlation.
    """
    sat = np.asarray(sat, float)
    radar = np.asarray(radar, float)
    with np.errstate(invalid="ignore"):
        sat_mask = (sat < sat_threshold) if sat_below else (sat > sat_threshold)
        radar_mask = radar > radar_threshold
    sat_mask &= np.isfinite(sat)
    radar_mask &= np.isfinite(radar)
    common = np.isfinite(sat) & np.isfinite(radar)
    if valid is not None:
        common &= valid

    signed = -sat if sat_below else sat
    dy, dx, r_lag = subcell_displacement(signed, radar, max_lag, common)
    return {
        "iou": iou(sat_mask, radar_mask, common),
        "pearson": pearson(signed, radar, common),
        "mutual_info": mutual_information(sat, radar, bins, common, normalized=True),
        "lag_dy": int(round(dy)),
        "lag_dx": int(round(dx)),
        "lag_dy_sub": round(float(dy), 2),
        "lag_dx_sub": round(float(dx), 2),
        "lag_r": r_lag,
    }
