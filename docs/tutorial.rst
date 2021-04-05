Using the diyepw package
================================================================

1. Identify the year(s) you want to cover with your weather files.
1. Identify the WMO weather station ID number(s) for the location(s) you want to cover.
1. Create the weather files at the command line:
    1. Install diyepw using pip by typing pip install diyepw in your console.
    1. Start Python and type import diyepw to work with this package.
    1. Ask for the file(s) you want:
    
        `diyepw.create_amy_epw_files_for_years_and_wmos(
        [{years}],
        [{WMOs}], 
        max_records_to_interpolate={integer}, 
        max_records_to_impute={integer}, 
        max_missing_amy_rows={integer}, 
        allow_downloads={Boolean},
        amy_epw_dir=’{dir}’
        )`



Example 1
----------------------------------
