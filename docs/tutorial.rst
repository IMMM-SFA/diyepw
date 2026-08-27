Tutorial: step-by-step examples using DIYEPW
================================================================

1. Identify the year(s) you want to cover with your weather files.
2. Identify the WMO weather station ID number(s) for the location(s) you want to cover.
3. Install ``diyepw`` package using pip.

Type in your console:
::

    pip install diyepw
  
4. Start Python and type ``import diyepw`` to begin working with this package.
5. Ask ``'diyepw`` to create the file(s) you want.

Your call to ``diyepw`` will include:
::

     import diyepw

     diyepw.create_amy_epw_files_for_years_and_wmos(
       [{years}],
       [{WMOs}],
       max_records_to_interpolate={integer},
       max_records_to_impute={integer},
       max_missing_amy_rows={integer},
       allow_downloads={Boolean},
       amy_epw_dir='{dir}',
       source='{auto|isd_lite|ghcnh}',
       station_id='{optional GHCN station id}',
     )

You'll need to provide to `diyepw` in this call:

- ``[{years}]``, where ``{years}`` is replaced with the 4-digit year(s) for which you want to produce a weather file (separated by commas).
   - ``diyepw`` creates the weather file for a calendar year based on the local time at the location of the weather station you selected.
- ``[{WMOs}]``, where ``{WMOs}`` is replaced with the WMO station identifier number(s) for which you want to produce a weather file (separated by commas).

You'll want to provide to ``diyepw`` in this call:

- ``max_records_to_interpolate={integer}``, where ``{integer}`` is replaced with the maximum number of records in the weather data that you want handled by interpolation. 
- ``max_records_to_impute={integer}``, where ``{integer}`` is replaced with the maximum number of records in the weather data that you want handled by imputation. 
- ``max_missing_amy_rows={integer}``, where ``{integer}`` is replaced with the maximum total number of missing rows that you want to allow in the weather data used to create the AMY file. 
- ``allow_downloads={True}``, which will give ``diyepw`` permission to go download the weather data that you need.
   - Your internet connection must be active for ``diyepw`` to do this. 
- ``amy_epw_dir='{dir}'``, where ``{dir}`` is replaced with the file path to the directory where you want your output EPWs (and any error files) to be stored.
   - Even if you don’t provide a file path, ``diyepw`` will return the location where it stored the output files at the console after it creates them.
- ``source='{auto|isd_lite|ghcnh}'`` (optional, default ``'auto'``) selects the AMY data source.
   - ``'auto'`` tries NOAA's legacy ISD-Lite product first and transparently falls back to NCEI's
     replacement GHCN-hourly (GHCNh) product when the ISD-Lite file is missing or too incomplete.
     NOAA stopped updating ISD-Lite in August 2025, so GHCNh is required for current-year data.
   - ``'isd_lite'`` forces ISD-Lite (legacy behavior).
   - ``'ghcnh'`` forces GHCNh (GHCN-hourly PSV files from NCEI).
- ``station_id='{GHCN ID}'`` (optional). GHCNh identifies stations by GHCN IDs (e.g. ``'USW00024233'``
  for Seattle-Tacoma) rather than WMO indices. ``diyepw`` ships with a WMO-to-GHCN map for most
  stations whose ISD-Lite WMO codes have a published GHCN counterpart. Pass an explicit
  ``station_id`` only when your station is not covered by that map.
  
We have example scenarios below with tutorials explaining how to use the diyepw package to create actual meteorological year EnergyPlus weather files that will meet the modeler’s needs.

These tutorials don’t assume that you are a Python programmer, although you will need to have Python installed and you will need to some basic familiarity with the command line. If you are a Python programmer, any of the workflows below can be embedded into your code once the diyepw package is imported.
  



Example 1: Making a single weather file
----------------------------------------------------------

Say that you designed an energy model for a building that was constructed in Chicago using the `EnergyPlus TMY3 EPW file for Chicago-O’Hare airport <https://energyplus.net/weather-location/north_and_central_america_wmo_region_4/USA/IL/USA_IL_Chicago-OHare.Intl.AP.725300_TMY3>`_. Now the building has been in operation for a full year and you want to calibrate your model using metered data.

**Identify year:** 2020

**Identify WMO weather station ID number:** Note that the name of the TMY weather file indicates the number of the WMO weather station data used to produce it.

    USA_IL_Chicago-OHare.Intl.AP.725300_TMY3.epw
    
The 6-digit number following “AP” is the WMO weather station ID number. North American WMO station ID numbers `will be 6 digits, starting with “7” <http://www.weathergraphics.com/identifiers/>`_. Here, we see that 725300 is the ID number for the weather station at Chicago-O’Hare International Airport. You can also open this file in a text editor and you will see that information on the first line.

**Create the weather files:** After installing and importing diyepw, enter this at the Python prompt:
::

    import diyepw
    diyepw.create_amy_epw_files_for_years_and_wmos(
      [2020],
      [725300],
      max_records_to_interpolate=6,
      max_records_to_impute=48,
      max_missing_amy_rows=5,
      allow_downloads=True,
      amy_epw_dir='./'
    )

To place the output somewhere besides the current directory, remember to change ``./`` to a path that exists and is valid on your computer to tell ``diyepw`` where to place its output AMY EPW files.

When diyepw has created the file, you will see this at the bottom of the console:
::

    {2020: {725300: ['./USA_IL_Chicago-OHare-Intl-AP.725300_AMY_2020.epw']}}


    
Example 2a: Making weather files for multiple locations in multiple years
--------------------------------------------------------------------------------

Now you want to get weather files for two different locations in Washington state: the first in Seattle and the second in the Tri-Cities region (comprised of Kennewick, Pasco, and Richland). You want to create weather files over three historical years, 2015-2017.

**Identify years:** 2015, 2016, and 2017

**Identify WMO weather station numbers:** If you don’t know the weather station number, take look at the `EnergyPlus weather page <https://energyplus.net/weather>`_ and navigate to the location of interest. On the page for `Washington state <https://energyplus.net/weather-region/north_and_central_america_wmo_region_4/USA/WA>`_, we see that 727930 is the ID number provided for the weather station at Seattle-Tacoma International Airport and 727845 is the number for the Pasco Tri-Cities Airport. 

**Create the weather files:** After installing and importing diyepw, enter this at the Python prompt:
::

    diyepw.create_amy_epw_files_for_years_and_wmos(
      [2016,2017,2018],
      [727930,727845],
      max_records_to_interpolate=6,
      max_records_to_impute=48,
      max_missing_amy_rows=5,
      allow_downloads=True,
      amy_epw_dir='./'
    )

Change ``./`` to your local output path before running the code if you want the output somewhere besides the current directory.

You’ll see more text returned from diyepw as it creates six AMY EPW weather files. When it’s finished, you will see this at the bottom of the console:
::

{2015: {727930: ['./USA_WA_Seattle-Tacoma-Intl-AP.727930_AMY_2015.epw'], 727845: ['./USA_WA_Pasco-Tri-Cities-AP.727845_AMY_2015.epw']}, 2016: {727930: ['./USA_WA_Seattle-Tacoma-Intl-AP.727930_AMY_2016.epw'], 727845: ['./USA_WA_Pasco-Tri-Cities-AP.727845_AMY_2016.epw']}, 2017: {727930: ['./USA_WA_Seattle-Tacoma-Intl-AP.727930_AMY_2017.epw'], 727845: ['./USA_WA_Pasco-Tri-Cities-AP.727845_AMY_2017.epw']}}



Example 2b: Changing the keyword arguments in response to an error message
--------------------------------------------------------------------------------

You also want to get a weather files for the Tri-Cities region in the year 2019. So you enter:
::

    diyepw.create_amy_epw_files_for_years_and_wmos(
      [2019],
      [727845],
      max_records_to_interpolate=6,
      max_records_to_impute=48,
      max_missing_amy_rows=5,
      allow_downloads=True,
      amy_epw_dir='./'
    )
    
But now ``diyepw`` returns:
:: 

    Problem processing year 2019 and WMO index 727845: File is missing 6 rows, but maximum allowed is 5
    2021-04-01 22:19:50,990 AMY EPW files could not be generated for 1 year/WMO Index combinations - see ./errors.csv for more information
    {2019: {727845: []}}

This means that the file containing the observed weather data is missing 6 rows and because it’s above the threshold ``max_missing_amy_rows=5``, ``diyepw`` returned an error and did not create the weather file.

Say you decide that 6 consecutive missing values really isn’t any more worrisome than 5, and you change that parameter:
::

    diyepw.create_amy_epw_files_for_years_and_wmos(
      [2019],
      [727845],
      max_records_to_interpolate=6,
      max_records_to_impute=48,
      max_missing_amy_rows=6,
      allow_downloads=True,
      amy_epw_dir='./'
    )
    
Now diyepw successfully creates the file. You will see:
::

{2019: {727845: ['./USA_WA_Pasco-Tri-Cities-AP.727845_AMY_2019.epw']}}



Example 3: Generating AMY EPWs for 2025 (after NOAA's ISD-Lite was retired)
---------------------------------------------------------------------------------

NOAA stopped updating ISD-Lite around August 2025; files for stations in that year are typically
incomplete (only the months prior to the cutoff are populated). NCEI replaced ISD-Lite with the
Global Historical Climatology Network hourly (GHCNh) product.

With the default ``source='auto'``, ``diyepw`` tries ISD-Lite first and transparently falls back
to GHCNh when the ISD-Lite file is too sparse. For 2025 onwards you can usually just run:
::

    diyepw.create_amy_epw_files_for_years_and_wmos(
      [2021, 2022, 2023, 2024, 2025],
      [727930],
      max_records_to_interpolate=6,
      max_records_to_impute=48,
      max_missing_amy_rows=700,
      allow_downloads=True,
      amy_epw_dir='./'
    )

If you want to force the new product unconditionally, pass ``source='ghcnh'``:
::

    diyepw.create_amy_epw_files_for_years_and_wmos(
      [2025],
      [727930],
      allow_downloads=True,
      amy_epw_dir='./',
      source='ghcnh',
    )

GHCNh stations are identified by GHCN IDs (e.g. ``'USW00024233'`` for Seattle-Tacoma). The
``diyepw.wmo_to_ghcn_id()`` helper converts a 6-digit WMO index into the matching GHCN ID, and is
used implicitly by ``create_amy_epw_file`` when you pass ``source='ghcnh'`` without an explicit
``station_id``. For stations not covered by the packaged map, pass ``station_id='...'`` directly.

Why ``diyepw`` needs GHCNh: the August 2025 ISD-Lite continuity issue
---------------------------------------------------------------------------------

NOAA/NCEI **stopped updating ISD-Lite in August 2025** in favor of GHCNh. Practically:

* ISD-Lite files for 2025 are partial - typical files end in late August 2025 and contain only
  ~5,700 hourly rows out of 8,760, with thousands of consecutive missing hours after the cutoff.
* ISD-Lite files for 2026 and later do not exist on NOAA's servers at all (HTTP 404).

Without a second source, ``diyepw`` would either fail outright on years ``>= 2025`` or produce
EPWs with huge interpolated/imputed gaps. The GHCNh source was added so that
``create_amy_epw_file`` can keep producing accurate AMY EPWs past the ISD-Lite cutoff. GHCNh is
read from NCEI's object store as PSV (``GHCNh_<GHCN_ID>_<YEAR>.psv``), normalized into the same
canonical hourly schema as ISD-Lite, and run through the existing missing-value handling and EPW
writer.

Station identifier mapping (WMO <-> GHCN)
---------------------------------------------------------------------------------

When ``source='ghcnh'`` (or ``'auto'`` falls back to GHCNh), ``diyepw`` must translate the 6-digit
WMO index you pass into a GHCN station ID. It does this using ``diyepw.wmo_to_ghcn_id()``, backed
by the packaged file ``diyepw/data/ghcn_station_map.csv``.

How the map is built:

1. ``diyepw`` downloads NCEI's GHCN-hourly station inventory:
   ``https://www.ncei.noaa.gov/oa/global-historical-climatology-network/hourly/doc/ghcnh-station-list.txt``.
2. The inventory is fixed-width; the GHCN ID is in columns 1-11 and the WMO ID is in
   columns 81-86.
3. Rows whose WMO column is exactly five digits are kept.
4. The 5-digit WMO is multiplied by 10 to match NOAA's 6-digit ISD-Lite convention
   (``72793`` -> ``727930``).
5. The result is written as ``wmo_index,ghcn_id,name``.

Worked example - WMO ``727930`` -> GHCN ``USW00024233``:

::

    USW00024233  47.4447 -122.3144  112.5 WA SEATTLE TACOMA AP                      72793 US

The inventory shows ``USW00024233`` with WMO ``72793``. ``diyepw`` stores it as
``727930,USW00024233,SEATTLE TACOMA AP``.

A station may **not** be in the packaged map if NCEI's inventory leaves the WMO column blank,
lists a non-five-digit value, or duplicates an existing ``wmo_index``. In those cases pass
``station_id='<GHCN ID>'`` (e.g. ``USW00094846``) directly to
``create_amy_epw_files_for_years_and_wmos``.

To regenerate the packaged map from the latest NCEI inventory, delete
``diyepw/data/ghcn_station_map.csv`` and call any
``diyepw.wmo_to_ghcn_id(<wmo>, allow_downloads=True)`` lookup. To extend the map with custom rows
for stations NCEI does not list with a usable WMO ID, append them manually using the same
``wmo_index,ghcn_id,name`` schema.
