data/
=====

Packaged data resources used by the `diyepw` runtime.

`ghcn_station_map.csv`
----------------------

A precomputed mapping between **6-digit ISD-Lite WMO indices** (e.g. `727930`) and
**GHCN station identifiers** (e.g. `USW00024233`). Used by
`diyepw.wmo_to_ghcn_id()` so callers can keep passing WMO indices when the
GHCN-hourly (GHCNh) source is engaged.

### Why this file exists

NOAA/NCEI **stopped updating ISD-Lite in August 2025** in favor of GHCNh.
Without a second source `diyepw` would either fail outright on year `>= 2025`
or produce EPWs with huge gaps. GHCNh, however, identifies stations by GHCN
IDs rather than WMO indices, so a translation table is needed to keep the
public API stable. See the project README ("Station identifiers and the
WMO -> GHCN mapping") for the user-facing details.

### Schema

CSV with three columns:

| column      | type   | description                                          |
|-------------|--------|------------------------------------------------------|
| `wmo_index` | int    | NOAA ISD-Lite-style 6-digit WMO index.               |
| `ghcn_id`   | str    | GHCN-hourly station identifier (typically 11 chars). |
| `name`      | str    | Human-readable station name from the inventory.      |

### How the file is built

`diyepw.wmo_to_ghcn._build_map_from_inventory()` builds this CSV from NCEI's
GHCN-hourly station inventory:

1. Download `https://www.ncei.noaa.gov/oa/global-historical-climatology-network/hourly/doc/ghcnh-station-list.txt`
   (fixed-width text).
2. Parse with `pandas.read_fwf` using the fixed-width column specs in
   `wmo_to_ghcn.py` - the GHCN ID is in cols 1-11 and the WMO ID is in
   cols 81-86.
3. Keep only rows whose WMO field matches `^\d{5}$`.
4. Convert each 5-digit WMO ID to the 6-digit ISD-Lite-style index by
   multiplying by 10 (`72793` -> `727930`).
5. Sort by `wmo_index`, drop duplicates on `wmo_index`, and write
   `wmo_index,ghcn_id,name` rows here.

A station appears in the map **only** when its inventory line has a non-blank
WMO field that parses as exactly five digits. To regenerate from the latest
NCEI inventory, delete this file and call any
`diyepw.wmo_to_ghcn_id(<wmo>, allow_downloads=True)` lookup. To extend the
map with custom rows for stations NCEI does not list with a usable WMO ID,
append them manually using the same schema.

Other subdirectories
--------------------

- `noaa_isd_lite_files/` - cached ISD-Lite `.gz` downloads.
- `noaa_isd_lite_catalogs/` - cached yearly NOAA ISD-Lite directory listings.
- `tmy_epw_files/` - cached TMY3 EPW downloads from energyplus.net.
- `tmy_epw_catalogs/` - cached TMY3 station catalog.
- `ghcnh_files/` (created on demand) - cached GHCN-hourly PSV downloads.
