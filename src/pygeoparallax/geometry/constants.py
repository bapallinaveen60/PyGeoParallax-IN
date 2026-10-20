"""Earth and satellite constants used by the geometry modules (SI units)."""

# WGS84 ellipsoid
WGS84_A = 6378137.0  # semi-major axis [m]
WGS84_F = 1.0 / 298.257223563  # flattening
WGS84_B = WGS84_A * (1.0 - WGS84_F)  # semi-minor axis [m]
WGS84_E2 = WGS84_F * (2.0 - WGS84_F)  # first eccentricity squared
WGS84_EP2 = WGS84_E2 / (1.0 - WGS84_E2)  # second eccentricity squared

# Nominal geostationary orbit radius from Earth's centre [m]
GEO_RADIUS = 42164160.0

# Nominal sub-satellite longitudes [degrees east]
SATELLITE_LONGITUDES = {
    "INSAT-3DR": 74.0,
    "INSAT-3DS": 82.0,
}
