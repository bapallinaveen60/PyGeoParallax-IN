"""Satellite and solar viewing angles.

All angles are in degrees. Azimuths are measured clockwise from north, from
the ground point towards the satellite or the Sun.
"""

from __future__ import annotations

import numpy as np

from .constants import GEO_RADIUS
from .ecef import enu_basis, geodetic_to_ecef


def satellite_view_angles(lat, lon, sat_lon, h=0.0, sat_radius=GEO_RADIUS):
    """Viewing zenith and azimuth angles of a geostationary satellite.

    Parameters
    ----------
    lat, lon : array_like
        Geodetic latitude and longitude of the ground point (or cloud top).
    sat_lon : float
        Sub-satellite longitude, e.g. ``SATELLITE_LONGITUDES["INSAT-3DR"]``.
    h : array_like, optional
        Ellipsoidal height of the point [m], e.g. terrain or cloud-top height.
    sat_radius : float, optional
        Satellite distance from Earth's centre [m].

    Returns
    -------
    vza, vaa : ndarray
        Viewing zenith angle and viewing azimuth angle. VZA above 90 means the
        satellite is below the horizon.
    """
    gx, gy, gz = geodetic_to_ecef(lat, lon, h)
    sat_lon_r = np.radians(sat_lon)
    los = np.stack([
        sat_radius * np.cos(sat_lon_r) - gx,
        sat_radius * np.sin(sat_lon_r) - gy,
        np.zeros_like(gz) - gz,
    ])
    east, north, up = enu_basis(lat, lon)
    e = np.sum(los * east, axis=0)
    n = np.sum(los * north, axis=0)
    u = np.sum(los * up, axis=0)
    vza = np.degrees(np.arctan2(np.hypot(e, n), u))
    vaa = np.degrees(np.arctan2(e, n)) % 360.0
    return vza, vaa


def _julian_century(time):
    t = np.asarray(time, dtype="datetime64[ns]")
    days = (t - np.datetime64("2000-01-01T12:00:00", "ns")) / np.timedelta64(1, "D")
    return days / 36525.0


def solar_angles(time, lat, lon):
    """Solar zenith and azimuth angles (NOAA solar position algorithm).

    Ignores atmospheric refraction. Accurate to about 0.01 degrees between
    1800 and 2100, which is far more than needed for day/night masks and
    shadow geometry.

    Parameters
    ----------
    time : datetime64 or array_like of datetime64
        UTC time; it is broadcast against ``lat``/``lon``.
    lat, lon : array_like
        Geodetic latitude and longitude.

    Returns
    -------
    sza, saa : ndarray
    """
    jc = _julian_century(time)
    t = np.asarray(time, dtype="datetime64[ns]")
    minutes_utc = (t - t.astype("datetime64[D]")) / np.timedelta64(1, "m")

    l0 = (280.46646 + jc * (36000.76983 + jc * 0.0003032)) % 360.0
    m = np.radians(357.52911 + jc * (35999.05029 - 0.0001537 * jc))
    ecc = 0.016708634 - jc * (0.000042037 + 0.0000001267 * jc)
    centre = (
        np.sin(m) * (1.914602 - jc * (0.004817 + 0.000014 * jc))
        + np.sin(2 * m) * (0.019993 - 0.000101 * jc)
        + np.sin(3 * m) * 0.000289
    )
    omega = np.radians(125.04 - 1934.136 * jc)
    app_long = np.radians(l0 + centre - 0.00569 - 0.00478 * np.sin(omega))
    mean_obliq = 23.0 + (26.0 + (21.448 - jc * (46.815 + jc * (0.00059 - jc * 0.001813))) / 60.0) / 60.0
    obliq = np.radians(mean_obliq + 0.00256 * np.cos(omega))
    decl = np.arcsin(np.sin(obliq) * np.sin(app_long))

    y = np.tan(obliq / 2) ** 2
    l0r = np.radians(l0)
    eqtime = 4.0 * np.degrees(
        y * np.sin(2 * l0r)
        - 2 * ecc * np.sin(m)
        + 4 * ecc * y * np.sin(m) * np.cos(2 * l0r)
        - 0.5 * y**2 * np.sin(4 * l0r)
        - 1.25 * ecc**2 * np.sin(2 * m)
    )  # equation of time [minutes]

    true_solar_time = (minutes_utc + eqtime + 4.0 * np.asarray(lon)) % 1440.0
    ha = np.radians(true_solar_time / 4.0 - 180.0)
    lat_r = np.radians(lat)

    cos_sza = np.sin(lat_r) * np.sin(decl) + np.cos(lat_r) * np.cos(decl) * np.cos(ha)
    sza = np.degrees(np.arccos(np.clip(cos_sza, -1.0, 1.0)))
    saa = (
        np.degrees(np.arctan2(np.sin(ha), np.cos(ha) * np.sin(lat_r) - np.tan(decl) * np.cos(lat_r)))
        + 180.0
    ) % 360.0
    return sza, saa
