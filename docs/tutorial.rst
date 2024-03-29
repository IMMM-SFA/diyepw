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
       amy_epw_dir='{dir}'
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

