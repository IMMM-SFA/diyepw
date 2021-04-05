Using the diyepw package
================================================================

1. Identify the year(s) you want to cover with your weather files.
2. Identify the WMO weather station ID number(s) for the location(s) you want to cover.
3. Install ``diyepw`` package using pip.

Type in your console:
::

    pip install diyepw
  
4. Start Python and type import diyepw to work with this package.
5. Ask ``'diyepw`` to create the file(s) you want.
  
Your call to ``diyepw`` will include:
::
  
     diyepw.create_amy_epw_files_for_years_and_wmos(
     [{years}],
     [{WMOs}], 
     max_records_to_interpolate={integer}, 
     max_records_to_impute={integer}, 
     max_missing_amy_rows={integer}, 
     allow_downloads={Boolean},
     amy_epw_dir=’{dir}’
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
   - If you don’t provide a file path, ``diyepw`` will return the location where it stored the output files at the console after it creates them.
  
We have three example scenarios below. Each one has a tutorial explaining how to use the diyepw package to create actual meteorological year EnergyPlus weather files that meet the modeler’s needs.

These tutorials don’t assume that you are a Python programmer, although you will need to have Python installed and you will need to some basic familiarity with the command line. If you are a Python programmer, any of the workflows below can be embedded into your code once the diyepw package is imported.
  


Example 1: Making a single weather file
----------------------------------------------------------

Say that you designed an energy model for a building that was constructed in Chicago using the `EnergyPlus TMY3 weather file for Chicago-O’Hare airport <https://energyplus.net/weather-location/north_and_central_america_wmo_region_4/USA/IL/USA_IL_Chicago-OHare.Intl.AP.725300_TMY3>`_. Now the building has been in operation for a full year and you want to calibrate your model using metered data.

**Identify year:** 2020

**Identify WMO weather station ID number:** Note that the TMY weather file indicates the number of the WMO weather station data that was used to produce it.

    USA_IL_Chicago-OHare.Intl.AP.725300_TMY3.epw
    
The 6-digit number following “AP” is the WMO weather station ID number. North American WMO station ID numbers `will be 6 digits, starting with “7” <https://tgftp.nws.noaa.gov/logs/site.shtml>`_. Here, we see that 725300 is the ID number for the weather station at Chicago-O’Hare International Airport. You can also open this file in a text editor and you will see that information on the first line.


