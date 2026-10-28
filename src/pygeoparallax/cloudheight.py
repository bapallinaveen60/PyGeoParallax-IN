"""Cloud-top height from brightness temperature or pressure, using a temperature profile.

For an opaque cloud, the 10.8 um brightness temperature (TIR1) is close to the
cloud-top temperature, so the cloud-top height is the height where the
atmosphere has that temperature. This module does that lookup against a
vertical profile: the AFGL tropical standard atmosphere for now, and ERA5
profiles once they are available.

Known limits:

* Thin cirrus is partly transparent. Its BT is warmer than its true top, so
  its height is underestimated.
* BT colder than the tropopause minimum (overshooting tops) is assigned the
  tropopause height.
* Pressure-level heights in a standard atmosphere differ from the real
  atmosphere by a few hundred metres.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Profile:
    """A vertical atmospheric profile, ordered from the surface upwards."""

    height: np.ndarray  # m above sea level
    temperature: np.ndarray  # K
    pressure: np.ndarray  # hPa

    @property
    def tropopause_index(self) -> int:
        """Index of the temperature minimum (the cold-point tropopause)."""
        return int(np.argmin(self.temperature))

    @property
    def tropopause_height(self) -> float:
        return float(self.height[self.tropopause_index])


# AFGL tropical standard atmosphere (Anderson et al. 1986; McClatchey et al. 1972), 0-25 km.
_TROP_Z_KM = np.arange(0, 26, 1.0)
_TROP_T = np.array([
    299.7, 293.7, 287.7, 283.7, 277.0, 270.3, 263.6, 257.0, 250.3, 243.6,
    237.0, 230.1, 223.6, 217.0, 210.3, 203.7, 197.0, 194.8, 198.8, 202.7,
    206.7, 210.7, 214.6, 217.0, 219.2, 221.4,
])
_TROP_P = np.array([
    1013.0, 904.0, 805.0, 715.0, 633.0, 559.0, 492.0, 432.0, 378.0, 329.0,
    286.0, 247.0, 213.0, 182.0, 156.0, 132.0, 111.0, 93.7, 78.9, 66.6,
    56.5, 48.0, 40.9, 35.0, 30.0, 25.7,
])

#: AFGL tropical standard atmosphere.
TROPICAL = Profile(height=_TROP_Z_KM * 1000.0, temperature=_TROP_T, pressure=_TROP_P)


def height_from_temperature(temperature, profile: Profile = TROPICAL):
    """Height [m] where the profile's troposphere has the given temperature.

    Only the troposphere (surface to the tropopause) is used, where temperature
    falls with height so the lookup is unique. Temperatures colder than the
    tropopause give the tropopause height; warmer than the surface give 0 m.
    NaN stays NaN.
    """
    k = profile.tropopause_index
    # np.interp needs increasing x: reverse the tropospheric part (temperature decreases upwards).
    t = profile.temperature[: k + 1][::-1]
    z = profile.height[: k + 1][::-1]
    temperature = np.asarray(temperature, float)
    out = np.interp(temperature, t, z, left=z[0], right=z[-1])
    return np.where(np.isnan(temperature), np.nan, out)


def height_from_pressure(pressure, profile: Profile = TROPICAL):
    """Height [m] of a pressure level [hPa], interpolating linearly in log(pressure)."""
    pressure = np.asarray(pressure, float)
    logp = np.log(profile.pressure[::-1])
    z = profile.height[::-1]
    with np.errstate(invalid="ignore", divide="ignore"):
        out = np.interp(np.log(pressure), logp, z, left=z[0], right=z[-1])
    return np.where(np.isfinite(pressure) & (pressure > 0), out, np.nan)


def cloud_mask(bt, clear_sky_bt=None, delta=8.0, threshold=270.0):
    """Cloudy where the 10.8 um BT is well below clear sky.

    Parameters
    ----------
    bt : array_like
        TIR1 brightness temperature [K].
    clear_sky_bt : array_like, optional
        Expected clear-sky BT [K] on the same grid, e.g. ISRO's CSBT_TIR1
        sampled to the pixels. Pixels more than ``delta`` colder are cloudy.
        Where it is NaN or not given, the fixed ``threshold`` is used.
    delta : float, optional
        Required BT depression below clear sky [K].
    threshold : float, optional
        Fallback: BT below this is cloudy [K].
    """
    bt = np.asarray(bt, float)
    with np.errstate(invalid="ignore"):
        fixed = bt < threshold
        if clear_sky_bt is None:
            return fixed & np.isfinite(bt)
        csbt = np.asarray(clear_sky_bt, float)
        relative = bt < csbt - delta
        return np.where(np.isfinite(csbt), relative, fixed) & np.isfinite(bt)


def cloud_top_height(bt, clear_sky_bt=None, profile: Profile = TROPICAL, **mask_kwargs):
    """Per-pixel cloud-top height [m] from TIR1 BT: profile lookup where cloudy, NaN elsewhere."""
    mask = cloud_mask(bt, clear_sky_bt, **mask_kwargs)
    return np.where(mask, height_from_temperature(bt, profile), np.nan)


def height_from_temperature_profiles(temperature, profile_t, profile_z, min_pressure_index=None):
    """Like :func:`height_from_temperature`, with a separate profile for each value.

    Parameters
    ----------
    temperature : array_like, shape (n,)
        Temperatures to look up [K].
    profile_t, profile_z : array_like, shape (n, levels)
        Temperature [K] and height [m] of each value's profile, ordered from
        the surface upwards.
    min_pressure_index : int, optional
        Highest level allowed as the tropopause (e.g. the 70 hPa index), so a
        warm stratosphere above is never searched. Defaults to all levels.

    The lookup runs downwards from each profile's cold-point tropopause and
    takes the first level at least as warm as the value, interpolating linearly
    in between. Searching from the top keeps low-level inversions from
    capturing high clouds. Colder than the cold point gives the cold-point
    height; warmer than the lowest level gives that level's height.
    """
    t = np.asarray(temperature, float).ravel()
    pt = np.asarray(profile_t, float)
    pz = np.asarray(profile_z, float)
    n_lev = pt.shape[1]
    top = n_lev if min_pressure_index is None else min_pressure_index + 1
    idx = np.arange(n_lev)
    cold = np.argmin(np.where(idx < top, pt, np.inf), axis=1)
    rows = np.arange(t.size)
    # Highest level at or below the cold point that is at least as warm as the value.
    warm = (pt >= t[:, None]) & (idx <= cold[:, None])
    # Colder than the cold point: k is the cold point itself, so the height is the cold-point height.
    k = n_lev - 1 - np.argmax(warm[:, ::-1], axis=1)
    found = warm.any(axis=1)  # False only if warmer than every level
    k = np.where(found, k, 0)
    k1 = np.minimum(k + 1, cold)
    t0, t1 = pt[rows, k], pt[rows, k1]
    z0, z1 = pz[rows, k], pz[rows, k1]
    with np.errstate(invalid="ignore", divide="ignore"):
        frac = np.where(t0 > t1, (t0 - t) / (t0 - t1), 0.0)
    out = z0 + np.clip(frac, 0.0, 1.0) * (z1 - z0)
    out = np.where(found, out, pz[:, 0])  # warmer than every level
    return np.where(np.isnan(t), np.nan, out).reshape(np.shape(temperature))


def cloud_top_height_profiles(bt, lat, lon, profiles, clear_sky_bt=None, min_pressure=70.0, **mask_kwargs):
    """Per-pixel cloud-top height [m] using gridded profiles, e.g. ERA5.

    Parameters
    ----------
    bt, lat, lon : array_like
        TIR1 brightness temperature [K] and pixel positions [degrees].
    profiles : xarray.Dataset
        ``temperature`` and ``height`` on ``(level, lat, lon)``, surface first,
        as from :func:`pygeoparallax.ingest.read_era5_profiles`. Profiles are
        interpolated bilinearly to each pixel.
    clear_sky_bt, **mask_kwargs
        Cloud mask, as in :func:`cloud_mask`.
    min_pressure : float, optional
        Highest pressure level [hPa] searched for the cold-point tropopause.
    """
    from scipy.interpolate import RegularGridInterpolator

    bt = np.asarray(bt, float)
    mask = cloud_mask(bt, clear_sky_bt, **mask_kwargs)
    out = np.full(bt.shape, np.nan)
    if not mask.any():
        return out
    levels = profiles["level"].values
    top = int(np.flatnonzero(levels >= min_pressure).max())
    grid = (profiles["lat"].values, profiles["lon"].values)
    pts = np.stack([np.asarray(lat, float)[mask], np.asarray(lon, float)[mask]], -1)
    prof = {}
    for name in ("temperature", "height"):
        values = np.moveaxis(profiles[name].values, 0, -1)  # (lat, lon, level)
        prof[name] = RegularGridInterpolator(grid, values, bounds_error=False, fill_value=None)(pts)
    out[mask] = height_from_temperature_profiles(bt[mask], prof["temperature"], prof["height"], top)
    return out


def effective_height(cth, scale=1.0, offset=0.0):
    """Height to correct with when the target is not the infrared cloud top [m].

    ``scale * cth - offset``, floored at 0 m; NaN (clear sky) stays NaN.

    The BT-derived height is the top of the cloud, which is right for cloud
    products. Precipitation sits lower: against GPM DPR over India, the
    coldest convective tops were a median 3.2 km above the Ku-band storm top
    (this project's GPM validation, 2018-2024: medians 16.6 and 11.9 km in
    206 cells). For rain-related products an ``offset`` of about 3000 m, or a
    ``scale`` near 0.7, moves the signal to the precipitating level instead.
    These values are a starting point, not a calibration.
    """
    cth = np.asarray(cth, float)
    with np.errstate(invalid="ignore"):
        return np.where(np.isfinite(cth), np.maximum(scale * cth - offset, 0.0), np.nan)
