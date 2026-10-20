"""Numba kernel for :func:`pygeoparallax.geometry.parallax.parallax_correct`.

Same algorithm as the numpy implementation (enlarged ellipsoid, then Newton
refinement), but fused per pixel and run in parallel, so no large temporary
arrays are created.
"""

from __future__ import annotations

import math

import numpy as np
from numba import njit, prange

from .constants import WGS84_A, WGS84_B, WGS84_E2, WGS84_EP2

_DEG = math.pi / 180.0


@njit(cache=True, inline="always")
def _to_ecef(lat, lon, h):
    sl = math.sin(lat)
    cl = math.cos(lat)
    n = WGS84_A / math.sqrt(1.0 - WGS84_E2 * sl * sl)
    return (n + h) * cl * math.cos(lon), (n + h) * cl * math.sin(lon), (n * (1.0 - WGS84_E2) + h) * sl


@njit(cache=True, inline="always")
def _to_geodetic(x, y, z):
    lon = math.atan2(y, x)
    p = math.hypot(x, y)
    beta = math.atan2(WGS84_A * z, WGS84_B * p)
    lat = 0.0
    for _ in range(3):
        sb = math.sin(beta)
        cb = math.cos(beta)
        lat = math.atan2(z + WGS84_EP2 * WGS84_B * sb * sb * sb, p - WGS84_E2 * WGS84_A * cb * cb * cb)
        beta = math.atan2(WGS84_B * math.sin(lat), WGS84_A * math.cos(lat))
    sl = math.sin(lat)
    n = WGS84_A / math.sqrt(1.0 - WGS84_E2 * sl * sl)
    h = p * math.cos(lat) + z * sl - WGS84_A * WGS84_A / n
    return lat, lon, h


@njit(cache=True, inline="always")
def _up_dot(lat, lon, dx, dy, dz):
    cl = math.cos(lat)
    return dx * cl * math.cos(lon) + dy * cl * math.sin(lon) + dz * math.sin(lat)


@njit(parallel=True, cache=True)
def correct_kernel(lat, lon, height, h0, sat_x, sat_y, newton_iterations, out_lat, out_lon):
    for i in prange(lat.size):
        h = height[i]
        out_lat[i] = np.nan
        out_lon[i] = np.nan
        if not math.isfinite(h):
            continue
        la = lat[i] * _DEG
        lo = lon[i] * _DEG
        px, py, pz = _to_ecef(la, lo, h0[i])
        dx = sat_x - px
        dy = sat_y - py
        dz = -pz
        norm = math.sqrt(dx * dx + dy * dy + dz * dz)
        dx /= norm
        dy /= norm
        dz /= norm
        if _up_dot(la, lo, dx, dy, dz) <= 0.0:
            continue  # behind the limb

        a2 = (WGS84_A + h) ** 2
        b2 = (WGS84_B + h) ** 2
        qa = (dx * dx + dy * dy) / a2 + dz * dz / b2
        qb = 2.0 * ((px * dx + py * dy) / a2 + pz * dz / b2)
        qc = (px * px + py * py) / a2 + pz * pz / b2 - 1.0
        disc = qb * qb - 4.0 * qa * qc
        if disc < 0.0:
            continue
        if qc == 0.0:
            t = 0.0
        else:
            q = -0.5 * (qb + math.copysign(math.sqrt(disc), qb))
            r1 = q / qa
            r2 = qc / q
            t = r1 if abs(r1) < abs(r2) else r2

        for _ in range(newton_iterations):
            qlat, qlon, qh = _to_geodetic(px + t * dx, py + t * dy, pz + t * dz)
            t += (h - qh) / _up_dot(qlat, qlon, dx, dy, dz)

        qlat, qlon, _ = _to_geodetic(px + t * dx, py + t * dy, pz + t * dz)
        out_lat[i] = qlat / _DEG
        out_lon[i] = qlon / _DEG
