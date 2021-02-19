# DIYEPW
DIYEPW is a tool developed by Pacific Northwest National Laboratory that allows the quick and easy
generation of a set of EPW files for a given set of WMOs and years. It is provided as both a set
of scripts (https://github.com/IMMM-SFA/diyepw-scripts) and as a Python package (https://github.com/IMMM-SFA/diyepw).
This allows DIYEPW to be used as a command-line tool, or as a package to incorporate EPW file 
generation into a custom script.

# Getting Started
The DIYEPW Python package can be easily installed using PIP:

```
pip install diyepw
```

One you've installed the package, you can access any of the DIYEPW functions or classes by importing the package
into your own Python scripts:

```
import diyepw
diyepw.create_amy_epw_files_for_years_and_wmos(
    [2010, 2011, 2012],
    [724940, 725300], 
    max_records_to_interpolate=10, 
    max_records_to_impute=25, 
    max_missing_amy_rows=5, 
    allow_downloads=True
)
```

# Using DIYEPW to generate AMY EPW files
This package is a tool for the generation of AMY (actual meteorological year) EPW files, which is done
by injecting AMY data into TMY (typical meteorological year) EPW files. The generated EPW files
have the following fields replaced with observed data:

1. dry bulb temperature
1. dew point temperature
1. pressure
1. wind direction
1. wind speed

Because observed weather data commonly contains gaps, DIYEPW will attempt to fill in any such gaps to ensure that in 
each record a value is present for all of the hourly timestamps for the variables shown above. To do so, it will use one 
of two strategies to impute or interpolate values for any missing fields in the data set:

#### Interpolation: Handling for small gaps
Small gaps (by default up to 6 consecutive hours of consecutive missing data for a field), are handled by linear 
interpolation, so that for example if the dry bulb temperature has a gap with neighboring observed values like 
(20, X, X, X, X, 25), DIYEPW will replace the missing values to give (20, 21, 22, 23, 24, 25).

#### Imputation: Handling for large gaps
Large gaps (by default up to 48 consecutive hours of missing data for a field) are filled using an imputation strategy
whereby each missing field is set to the average of the field's value two weeks in the past and in the future from
the missing timestamp.

If a gap exists in the data that is larger than the maximum allowed for the imputation strategy, that file will be
rejected and no EPW file will be generated.

The maximum number of missing values that the interpolation strategy will be used for, and the maximum number of
missing values that can be imputed, can be changed from their defaults. The functions that generate EPW files, 
`create_amy_epw_file()` and `create_amy_epw_files_for_years_and_wmos()`, both accept the optional arguments
`max_records_to_interpolate` and `max_records_to_impute`, which likewise override the defaults of 6 and 48.
  
## Package Functions
All of the functionality of the DIYEPW project is available as a set of functions that underlie the scripts 
described above. The functions offer much more granular access to the capabilities of the project, and allow
DIYEPW capabilites to be incorporated into other software projects.

The functions provided by the package are as follows:

- `analyze_noaa_isd_lite_file()` - Performs an analysis of a single NOAA ISD Lite file to determine whether it is suitable
    for use in generating an AMY EPW file.
- `analyze_noaa_isd_lite_files()` - Performs an analysis of a set of NOAA ISD Lite files to determine whether they are
    suitable for use in generating AMY EPW files. This function is equivalent to the `analyze_noaa_data.py` script.
- `create_amy_epw_file()` - Creates a single AMY EPW file for a given year and WMO index.
- `create_amy_epw_files_for_years_and_wmos()` - Creates a set of AMY EPW files for a set of years and WMO indices.
- `get_noaa_isd_lite_file()` - Downloads a NOAA ISD Lite file from the NOAA online catalog for a given year and WMO index
- `get_tmy_epw_file()` - Downloads a TMY EPW file from the EnergyPlus online catalog for a given WMO index
- `get_wmo_station_location()` - Retrieves the state and county associated with a weather station

The classes provided by the package are as follows:

`Meteorology` - Represents a collection of meteorological observations, supporting reading in and writing out those
    observations in a number of formats. Currently TMY3 and ISD Lite are supported as input types and EPW is supported
    as an output type, but there are plans for more input formats to be supported in upcoming releases.

For more detailed documentation of all parameters, return types, and behaviors of the above functions and classes,
please refer to the in-code documentation that heads each function's definition in the package.

## Reading in TMY3 files and writing EPW files
Functions for reading TMY3 files and writing EPW files within this script were adapted from the 
[LAF.py script](https://github.com/SSESLab/laf/blob/master/LAF.py) by Carlo Bianchi at the Site-Specific 
Energy Systems Lab repository.
