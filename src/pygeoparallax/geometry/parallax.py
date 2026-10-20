"""Parallax correction by ray tracing against the WGS84 ellipsoid.

A geostationary imager geolocates each pixel where the line of sight meets the
Earth's surface (the *apparent* position). A cloud at height ``h`` actually
sits on that same line of sight, but closer to the satellite. The corrected
position is the point on the line of sight at geodetic height ``h``.

The solver follows Bieliński (2020, Remote Sens. 12, 365):

1. Intersect the line of sight with the ellipsoid enlarged by ``h``
   (semi-axes ``a + h`` and ``b + h``). This is closed-form and accurate to
   centimetres.
2. Refine with Newton steps on the true geodetic height, which removes the
   remaining error.

Unlike satpy's spherical-Earth correction, the apparent position can sit on
terrain (``h0``) and :func:`parallax_correct_terrain` uses a DEM to clamp
cloud tops to the ground and to correct clear-sky terrain parallax.
"""

from __future__ import annotations

import numpy as np
from pyproj import Geod

from .constants import GEO_RADIUS, WGS84_A, WGS84_B
from .ecef import ecef_to_geodetic, enu_basis, geodetic_to_ecef

_GEOD = Geod(ellps="WGS84")


def parallax_correct(lat, lon, height, sat_lon, h0=0.0, sat_radius=GEO_RADIUS,
                     newton_iterations=1, backend="numba"):
    """Move apparent pixel positions to the true position of features at ``height``.

    Parameters
    ----------
    lat, lon : array_like
        Apparent (navigated) geodetic latitude and longitude [degrees].
    height : array_like
        Ellipsoidal height of the observed feature, e.g. cloud-top height [m].
        NaN gives NaN output. Heights above mean sea level differ from this by
        the geoid undulation (about -50 to -100 m over India). This changes the
        shift by under 1%.
    sat_lon : float
        Sub-satellite longitude [degrees east].
    h0 : array_like, optional
        Height of the surface the navigation is referenced to [m]. This is 0
        for ellipsoid-navigated L1 data.
    sat_radius : float, optional
        Satellite distance from Earth's centre [m].
    newton_iterations : int, optional
        Refinement steps after the enlarged-ellipsoid solution. Without any,
        the error is about 1 cm for a 12 km cloud over India. One step brings it
        below a millimetre.
    backend : {"numba", "numpy"}, optional
        ``"numba"`` (default) runs a parallel compiled kernel. ``"numpy"`` is
        the vectorised reference implementation. Both give identical results.

    Returns
    -------
    lat_c, lon_c : ndarray
        Corrected latitude and longitude [degrees]. NaN where the height is NaN
        or the satellite cannot see the point.
    """
    lat, lon, height, h0 = np.broadcast_arrays(
        np.asarray(lat, float), np.asarray(lon, float),
        np.asarray(height, float), np.asarray(h0, float),
    )
    if backend == "numba":
        from ._parallax_numba import correct_kernel

        out_lat = np.empty(lat.size)
        out_lon = np.empty(lat.size)
        sat = np.radians(sat_lon)
        correct_kernel(
            np.ascontiguousarray(lat).ravel(), np.ascontiguousarray(lon).ravel(),
            np.ascontiguousarray(height).ravel(), np.ascontiguousarray(h0).ravel(),
            sat_radius * np.cos(sat), sat_radius * np.sin(sat), int(newton_iterations),
            out_lat, out_lon,
        )
        return out_lat.reshape(lat.shape), out_lon.reshape(lat.shape)
    if backend != "numpy":
        raise ValueError(f"unknown backend {backend!r}")
    return _parallax_correct_numpy(lat, lon, height, h0, sat_lon, sat_radius, newton_iterations)


def _parallax_correct_numpy(lat, lon, height, h0, sat_lon, sat_radius, newton_iterations):
    px, py, pz = geodetic_to_ecef(lat, lon, h0)
    sat = np.radians(sat_lon)
    dx = sat_radius * np.cos(sat) - px
    dy = sat_radius * np.sin(sat) - py
    dz = -pz
    norm = np.sqrt(dx**2 + dy**2 + dz**2)
    dx, dy, dz = dx / norm, dy / norm, dz / norm

    # Points behind the Earth's limb are not visible from the satellite.
    _, _, up = enu_basis(lat, lon)
    visible = (dx * up[0] + dy * up[1] + dz * up[2]) > 0.0

    # Step 1: intersect with the ellipsoid enlarged by `height`.
    a2 = (WGS84_A + height) ** 2
    b2 = (WGS84_B + height) ** 2
    qa = (dx**2 + dy**2) / a2 + dz**2 / b2
    qb = 2.0 * ((px * dx + py * dy) / a2 + pz * dz / b2)
    qc = (px**2 + py**2) / a2 + pz**2 / b2 - 1.0
    disc = qb**2 - 4.0 * qa * qc
    with np.errstate(invalid="ignore", divide="ignore"):
        # Numerically stable roots; take the one closest to the apparent point.
        q = -0.5 * (qb + np.copysign(np.sqrt(disc), qb))
        r1 = q / qa
        r2 = qc / q
        t = np.where(np.abs(r1) < np.abs(r2), r1, r2)
        t = np.where(qc == 0.0, 0.0, t)

        # Step 2: Newton refinement on the true geodetic height.
        for _ in range(newton_iterations):
            qlat, qlon, qh = ecef_to_geodetic(px + t * dx, py + t * dy, pz + t * dz)
            _, _, qup = enu_basis(qlat, qlon)
            t = t + (height - qh) / (dx * qup[0] + dy * qup[1] + dz * qup[2])

    lat_c, lon_c, _ = ecef_to_geodetic(px + t * dx, py + t * dy, pz + t * dz)
    bad = ~(visible & (disc >= 0.0) & np.isfinite(height))
    lat_c = np.where(bad, np.nan, lat_c)
    lon_c = np.where(bad, np.nan, lon_c)
    return lat_c, lon_c


def parallax_correct_terrain(lat, lon, cth, sat_lon, surface_height, cloudy=None,
                             iterations=3, **kwargs):
    """Terrain-aware parallax correction for cloudy and clear-sky pixels.

    Cloudy pixels move to their cloud-top height, clamped so a cloud is never
    below the ground beneath it. Clear pixels move to where the line of sight
    actually meets the terrain (terrain parallax). This matters over the
    Western Ghats and the Himalayas, where ellipsoid navigation misplaces
    even the ground by several kilometres.

    The ground height must be looked up at the *corrected* position, so the
    solution is found by fixed-point iteration. It converges when the terrain
    slope is less steep than the line of sight, which holds for VZA below
    about 70 degrees.

    Parameters
    ----------
    lat, lon : array_like
        Apparent (ellipsoid-navigated) latitude and longitude [degrees].
    cth : array_like
        Cloud-top height above the ellipsoid [m]. NaN for clear sky.
    sat_lon : float
        Sub-satellite longitude [degrees east].
    surface_height : callable
        ``surface_height(lat, lon) -> height [m]``, e.g. an interpolator over an
        SRTM grid. It must accept arrays and return ellipsoidal heights.
    cloudy : array_like of bool, optional
        Cloud mask. Defaults to ``isfinite(cth)``.
    iterations : int, optional
        Fixed-point iterations for the terrain height.
    **kwargs
        Passed to :func:`parallax_correct`.

    Returns
    -------
    lat_c, lon_c, height : ndarray
        Corrected position and the height that was used for it.
    """
    lat = np.asarray(lat, float)
    lon = np.asarray(lon, float)
    cth = np.asarray(cth, float)
    cloudy = np.isfinite(cth) if cloudy is None else np.asarray(cloudy, bool)

    lat_c, lon_c = lat, lon
    for _ in range(iterations):
        ground = np.asarray(surface_height(lat_c, lon_c), float)
        height = np.where(cloudy, np.fmax(cth, ground), ground)
        lat_c, lon_c = parallax_correct(lat, lon, height, sat_lon, **kwargs)
    return lat_c, lon_c, height


def parallax_shift(lat, lon, lat_c, lon_c):
    """Distance [m] and azimuth [degrees from north] from apparent to corrected position."""
    shape = np.broadcast(lat, lon, lat_c, lon_c).shape
    args = [np.broadcast_to(np.asarray(v, float), shape).ravel() for v in (lon, lat, lon_c, lat_c)]
    if args[0].size == 1:
        # pyproj < 3.8 converts 1-element arrays with float(), which NumPy deprecates.
        args = [float(a[0]) for a in args]
    az, _, dist = _GEOD.inv(*args)
    return np.reshape(dist, shape), np.reshape(np.asarray(az) % 360.0, shape)
