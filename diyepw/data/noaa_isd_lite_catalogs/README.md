data/noaa_isd_lite_catalogs
----------------------------
Lists of filenames of files for a year and WMO index. These catalog files are derived from
the NOAA ISD Lite website, and are stored here so that they don't have to be repeatedly
downloaded, as the webpage is quite large. If you want to re-download the file for a year,
just delete it before calling get_noaa_isd_lite_file(), or set the force_update argument
to True.