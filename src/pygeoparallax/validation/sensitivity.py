"""How cloud-top height errors propagate into the corrected position.

The parallax shift is roughly ``h * tan(VZA)``, so a CTH error ``dh`` moves
the corrected pixel by about ``dh * tan(VZA)``. At Agartala (VZA 34 deg) a
1 km CTH error is a ~0.7 km position error. These functions compute it
exactly with the full solver.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..geometry.parallax import parallax_correct, parallax_shift


def monte_carlo_shift(lat, lon, cth, sat_lon, sigma=1000.0, n=100, seed=0, **kwargs):
    """Random CTH perturbations -> spread of the corrected position.

    Each draw adds Gaussian noise with standard deviation ``sigma`` [m] to
    ``cth`` (clipped at 0) and re-runs the correction.

    Parameters
    ----------
    lat, lon, cth : array_like
        Apparent positions [degrees] and cloud-top heights [m].
    sat_lon : float
        Sub-satellite longitude [degrees east].
    sigma : float, optional
        CTH uncertainty (1 standard deviation) [m].
    n : int, optional
        Number of draws.
    seed : int, optional
        Random seed, so runs are reproducible.
    **kwargs
        Passed to :func:`parallax_correct`.

    Returns
    -------
    dict of ndarray
        ``shift_km`` (nominal shift), ``position_rmse_km`` (RMS distance of the
        perturbed positions from the nominal one) and ``position_p95_km``.
    """
    lat = np.asarray(lat, float)
    lon = np.asarray(lon, float)
    cth = np.asarray(cth, float)
    rng = np.random.default_rng(seed)

    lat_n, lon_n = parallax_correct(lat, lon, cth, sat_lon, **kwargs)
    shift, _ = parallax_shift(lat, lon, lat_n, lon_n)

    err = np.empty((n,) + lat.shape)
    for k in range(n):
        h = np.clip(cth + rng.normal(0.0, sigma, cth.shape), 0.0, None)
        lat_k, lon_k = parallax_correct(lat, lon, h, sat_lon, **kwargs)
        err[k], _ = parallax_shift(lat_n, lon_n, lat_k, lon_k)

    return {
        "shift_km": shift / 1000.0,
        "position_rmse_km": np.sqrt(np.mean(err**2, axis=0)) / 1000.0,
        "position_p95_km": np.percentile(err, 95, axis=0) / 1000.0,
    }


def bias_sweep(lat, lon, cth, sat_lon, offsets=(-2000.0, -1000.0, 1000.0, 2000.0), **kwargs):
    """Systematic CTH bias -> position error.

    Returns a DataFrame with one row per offset [m]: the mean, 95th-percentile
    and maximum position error [km] over all pixels with a valid CTH.
    """
    lat = np.asarray(lat, float)
    lon = np.asarray(lon, float)
    cth = np.asarray(cth, float)
    lat_n, lon_n = parallax_correct(lat, lon, cth, sat_lon, **kwargs)
    rows = []
    for off in offsets:
        lat_k, lon_k = parallax_correct(lat, lon, np.clip(cth + off, 0.0, None), sat_lon, **kwargs)
        d, _ = parallax_shift(lat_n, lon_n, lat_k, lon_k)
        d = d[np.isfinite(d)] / 1000.0
        rows.append({
            "offset_m": off,
            "mean_km": float(d.mean()) if d.size else np.nan,
            "p95_km": float(np.percentile(d, 95)) if d.size else np.nan,
            "max_km": float(d.max()) if d.size else np.nan,
        })
    return pd.DataFrame(rows).set_index("offset_m")
