# Data Access Notes

This document contains details on data sources, URLs, authentication steps, API configurations, and rate limits/quotas for the datasets utilized in the project.

---

## 1. INSAT-3DR (L1C Imager & Cloud Top Height)
*   **Source**: Meteorological and Oceanographic Satellite Data Archival Centre (MOSDAC) / ISRO
*   **URL**: [MOSDAC Portal](https://www.mosdac.gov.in/)
*   **Access Type**: FTP / HTTPS download API.
*   **Registration Steps**:
    1. Register on the MOSDAC website to obtain a username and password.
    2. Configure personal credentials in `~/.mosdac_auth` or environment variables:
       ```bash
       export MOSDAC_USERNAME="your_username"
       export MOSDAC_PASSWORD="your_password"
       ```
*   **Quota / Rate Limits**:
    *   Maximum concurrent connections: 2.
    *   Daily bulk download limits might apply during active operations.

---

## 2. ERA5 Atmospheric Reanalysis
*   **Source**: Copernicus Climate Data Store (CDS) / ECMWF
*   **URL**: [Copernicus CDS](https://cds.climate.copernicus.eu/)
*   **Access Type**: Python `cdsapi` client.
*   **Registration Steps**:
    1. Create an account at the Copernicus CDS Portal.
    2. Generate an API Key (UID and API Key).
    3. Save credentials in a file named `~/.cdsapirc`:
       ```ini
       url: https://cds.climate.copernicus.eu/api/v2
       key: <your_uid>:<your_api_key>
       ```
*   **Quota / Rate Limits**:
    *   Queued jobs are limited to 3-5 concurrent requests depending on system load.

---

## 3. GPM-DPR (2A.DPR Precipitation Radar)
*   **Source**: NASA EarthData / Precipitation Processing System (PPS)
*   **URL**: [NASA EarthData Search](https://search.earthdata.nasa.gov/) / [PPS FTPS](https://arthurhou.pps.eosdis.nasa.gov/)
*   **Access Type**: FTPS or HTTPS.
*   **Registration Steps**:
    1. Register for an Earthdata Login account.
    2. Add the "NASA PPS" application to your authorized applications.
    3. Access server: `arthurhou.pps.eosdis.nasa.gov` using your email address as both username and password.
*   **Quota / Rate Limits**:
    *   No strict data limit, but high rate concurrent downloads may result in temporary IP blocks.

---

## 4. IMD Doppler Weather Radar (DWR) Grids
*   **Source**: India Meteorological Department (IMD)
*   **URL**: [IMD Radar Data](https://mausam.imd.gov.in/)
*   **Access Type**: Manual download or customized scraping pipelines (Mumbai, Goa, Kochi, Agartala).
*   **Registration Steps**:
    *   For research, access is usually requested formally from IMD or downloaded from public radar portals.
*   **Quota / Rate Limits**:
    *   N/A (subject to availability).

---

## 5. SRTM DEM (30m Elevation)
*   **Source**: Shuttle Radar Topography Mission (SRTM) / USGS
*   **URL**: [USGS EarthExplorer](https://earthexplorer.usgs.gov/) or download directly via AWS open-data buckets.
*   **Access Type**: HTTPS / SpatioTemporal Asset Catalog (STAC).
*   **Registration Steps**:
    1. Use USGS EarthExplorer account to download tiles, or:
    2. Download tiles directly using Python packages like `elevation` or `dem-downloader` with public cloud mirrors.
