[![build](https://github.com/IMMM-SFA/diyepw/actions/workflows/build.yml/badge.svg)](https://github.com/IMMM-SFA/diyepw/actions/workflows/build.yml)
[![codecov](https://codecov.io/gh/IMMM-SFA/diyepw/branch/master/graph/badge.svg?token=IPOY8984MB)](https://codecov.io/gh/IMMM-SFA/diyepw)
[![DOI](https://zenodo.org/badge/290590032.svg)](https://zenodo.org/badge/latestdoi/290590032)
[![status](https://joss.theoj.org/papers/9267f12d29f6f17e6dce4fb7bb87897d/status.svg)](https://joss.theoj.org/papers/9267f12d29f6f17e6dce4fb7bb87897d)

# `diyepw`
`diyepw` is a tool developed by Pacific Northwest National Laboratory that allows the quick and easy
generation of a set of [EnergyPlus Weather (EPW) files](https://bigladdersoftware.com/epx/docs/8-3/auxiliary-programs/energyplus-weather-file-epw-data-dictionary.html) 
for a given set of [World Meteorological Organizations (WMOs) station identifiers](http://www.weathergraphics.com/identifiers/) 
and years.

EPW files are used as input into [EnergyPlus](https://energyplus.net/) building energy simulations, and have 
traditionally been difficult to work with using open source tools. `diyepw` aims to fill this gap by providing both 
a set of scripts and a Python package, allowing it to be used as a command-line tool or as a package to incorporate EPW 
file generation into other modules or custom scripts.

`diyepw` relies on the 
[National Oceanic and Atmospheric Administration (NOAA) Integrated Surface Database (ISD)](https://www.ncei.noaa.gov/products/land-based-station/integrated-surface-database) 
as the reference for EPW file generation, in particular the ISDLite repository which provides a subset of the data 
with eight surface parameters at hourly resolution.

Our freely available [Journal of Open Source Software paper](https://joss.theoj.org/papers/10.21105/joss.03313) describes the background of `diyepw` in more detail.

## Citing `diyepw`

### Paper

Amanda D. Smith, Benjamin Stürmer, Travis Thurber, & Chris R. Vernon. (2021). diyepw: A Python package for Do-It-Yourself EnergyPlus weather file generation. Journal of Open Source Software, 6(64), 3313, https://doi.org/10.21105/joss.03313

### Software

Amanda D. Smith, Benjamin Stürmer, Travis Thurber, & Chris R. Vernon. (2021). diyepw: A Python package for Do-It-Yourself EnergyPlus weather file generation. Zenodo. https://doi.org/10.5281/zenodo.5258122

# Getting Started
The `diyepw` Python package can be easily installed using PIP:

```
pip install diyepw
```

One you've installed the package, you can access any of the `diyepw` functions or classes by importing the package
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

EnergyPlus provides a nice user interface for finding weather station information using a 
map: [Browse Weather Data](https://energyplus.net/weather). Search using the map or the keyword input, and the WMO 
Index will be the six-digit number appearing in the `title` field. Alternatively, the identifiers are available as 
part of this dataset: [Weather Station Identifiers](http://www.weathergraphics.com/identifiers/). 

# Using `diyepw` to generate AMY EPW files
This package is a tool for the generation of AMY (actual meteorological year) EPW files, which is done
by injecting AMY data into TMY (typical meteorological year) EPW files. The generated EPW files
have the following fields replaced with observed data:

1. dry bulb temperature
1. dew point temperature
1. pressure
1. wind direction
1. wind speed

Because observed weather data commonly contains gaps, `diyepw` will attempt to fill in any such gaps to ensure that in 
each record a value is present for all of the hourly timestamps for the variables shown above. To do so, it will use one 
of two strategies to impute or interpolate values for any missing fields in the data set:

#### Interpolation: Handling for small gaps
Small gaps (by default up to 6 consecutive hours of consecutive missing data for a field), are handled by linear 
interpolation, so that for example if the dry bulb temperature has a gap with neighboring observed values like 
(20, X, X, X, X, 25), `diyepw` will replace the missing values to give (20, 21, 22, 23, 24, 25).

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
All of the functionality of the `diyepw` project is available as a set of functions that underlie the scripts 
described above. The functions offer much more granular access to the capabilities of the project, and allow
`diyepw` capabilites to be incorporated into other software projects.

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

## Scripts
This section describes the scripts available as part of this project. The scripts will be available in the terminal or
virtual environment after running `pip install diyepw`. The scripts are located in the `diyepw/scripts/` directory.
Every script has a manual page that can be accessed by passing the "--help" option to the script. For example:
 
```
analyze_noaa_data --help
```

### Workflow 1: AMY EPW generation based on years and WMO indices
This workflow uses only a single script, `create_amy_epw_files_for_years_and_wmos.py`, and
generates AMY EPW files for a set of years and WMO indices. It accomplishes this by combining
TMY (typical meteorological year) EPW files with AMY (actual meteorological year) data. The
TMY EPW file for a given WMO is downloaded by the software as needed from energyplus.net. The
AMY data comes from NOAA ISD Lite files that are likewise downloaded as needed, from 
ncdc.noaa.gov.

This script can be called like this:

```
create_amy_epw_files_for_years_and_wmos --years=2010-2015 --wmo-indices=723403,7722780 --output-path .
```

The options `--years` and `--wmo-indices` are required. You will be prompted for them if not provided in the arguments.
There are a number of other optional options that can also be set. All available options, their effects, and the values
they accept can be seen by calling this script with the `--help` option:

```
create_amy_epw_files_for_years_and_wmos --help
```

### Workflow 2: AMY EPW generation based on existing ISD Lite files
This workflow is very similar to Workflow 1, but instead of downloading NOAA's ISD Lite files
as needed, it reads in a set of ISD Lite files provided by the user and generates one AMY EPW
file corresponding to each.

This workflow involves two steps:

#### 1. analyze_noaa_data

The script analyze_noaa_data.py will check a set of ISD Lite files against a set of requirements,
and generate a CSV file listing the ISD Lite files that are suitable for conversion to EPW. The
script is called like this:

```
analyze_noaa_data --inputs=/path/to/your/inputs/directory --output-path .
```

The script will look for any file within the directory passed to --inputs, including in 
subdirectories or subdirectories of subdirectories. The files must be named like 
"999999-88888-2020.gz", where the first number is a WMO index and the final number is the
year - the middle number is ignored. The easiest way to get files that are suitable for use
for this script is to download them from NOAA's catalog at 
https://www1.ncdc.noaa.gov/pub/data/noaa/isd-lite/.

The ".gz" (gzip commpressed) format of the ISD Lite files is the format provided by NOAA,
but is not required. You may also provide ISD Lite files in CSV (.csv) format, or in a 
different compression format like ZIP (.zip). The file extension is used to determine what
format the file is and must match the file's format. Pass the `--help` option 
(`analyze_noaa_data --help`) for more information on what compressed formats are supported.

The script is primarily checking that the ISD Lite files are in concordance with the following limits:

1. Total number of rows missing
1. Maximum number of consecutive rows missing

and will produce the following files (as applicable) under the specified `--output-path`:

1. `missing_total_entries_high.csv`: A list of files where the total number of rows missing exceeds a threshold.
   The threshold is set to rule out files where more than 700 (out of 8760 total) entries are missing entirely
   by default, but a custom value can be set with the --max-missing-rows option:
       
    ```
    analyze_noaa_data --max-missing-rows=700
    ```
   
1. `missing_consec_entries_high.csv`: A list of files where the maximum consecutive number of rows missing exceeds 
   a threshold. The threshold is currently set to a maximum of 48 consecutive empty rows, but a custom value can 
   be set with the --max-consecutive-missing-rows option:
   
   ```
   analyze_noaa_data --max-consecutive-missing-rows=48
   ```
   
1. `files_to_convert.csv`: A list of the files that are deemed to be usable because they are neither missing too many
   total nor too many consecutive rows. This file determines which EPWs will be generated by the next script, and
   it can be freely edited before running that script.

#### 2. create_amy_epw_files

The script create_amy_epw.py reads the files_to_convert.csv file generated in the previous step, and for each
ISD Lite file listed, generates an AMY EPW file. It can be called like this:

```
create_amy_epw_files --max-records-to-interpolate=6 --max-records-to-impute=48
```

Both `--max-records-to-interpolate` and `--max-records-to-impute` are optional and can be used to override the
default size of the gaps that can be filled in observed data using the two strategies, which are described in more
detail at the top of this document.

## Reading in TMY3 files and writing EPW files
Functions for reading TMY3 files and writing EPW files within this script were adapted from the 
[LAF.py script](https://github.com/SSESLab/laf/blob/master/LAF.py) by Carlo Bianchi at the Site-Specific 
Energy Systems Lab repository.
