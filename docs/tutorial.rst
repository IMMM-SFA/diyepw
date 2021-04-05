Using the diyepw package
================================================================

1. Identify the year(s) you want to cover with your weather files.
2. Identify the WMO weather station ID number(s) for the location(s) you want to cover.
3. Install `diyepw` package using pip.

Type in your console:
::

    pip install diyepw
  
4. Start Python and type import diyepw to work with this package.
5. Ask `'diyepw` to create the file(s) you want.
  
Your call to `diyepw` will include:
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



Example 1
----------------------------------
