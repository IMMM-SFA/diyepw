import click
import diyepw
import os
import pandas as pd


@click.command()
@click.option(
    '--max-records-to-interpolate',
    default=6,
    show_default=True,
    type=int,
    help="""The maximum number of consecutive records to interpolate. See the documentation of the
            pandas.DataFrame.interpolate() method's "limit" argument for more details. Basically,
            if a sequence of fields up to the length defined by this argument are missing, those 
            missing values will be interpolated linearly using the values of the fields immediately 
            preceding and following the missing field(s). If a sequence of fields is longer than this
            limit, then those fields' values will be imputed instead (see --max-records-to-impute)
            """
)
@click.option(
    '--max-records-to-impute',
    default=48,
    show_default=True,
    type=int,
    help=f"""The maximum number of records to impute. For groups of missing records larger than the
            limit set by --max-records-to-interpolate but up to --max-records-to-impute, we replace the 
            missing values using the average of the value two weeks prior and the value two weeks after 
            the missing value. If there are more consecutive missing records than this limit, then the 
            file will not be processed, and will be added to the error file."""
)
@click.option(
    '-o', '--output-path',
    default='.',
    type=click.Path(
        file_okay=False,
        dir_okay=True,
        writable=True,
        resolve_path=True,
    ),
    help="""The path to which output and error files should be written."""
)
@click.argument(
    'path_to_station_list',
    default='./files_to_convert.csv',
    type=click.Path(
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        resolve_path=True,
    ),
)
def create_amy_epw_files(
    max_records_to_interpolate,
    max_records_to_impute,
    output_path,
    path_to_station_list,
):
    """Generate epw files based on the PATH_TO_STATION_LIST as generated by analyze_noaa_data.py, which must be called
       prior to this script. The generated files will be written to the designated --output-path. A list of any files
       that could not be generated due to validation or other errors will be written to errors.csv."""

    # Set path to outputs produced by this script.
    if not os.path.exists(output_path):
        os.mkdir(output_path)

    # Set path to the files where errors should be written
    errors_path = os.path.join(output_path, 'errors.csv')

    # Ensure that the errors file is truncated
    with open(errors_path, 'w'):
        pass

    # Read in list of AMY files that should be used to create EPW files.
    amy_file_list = pd.read_csv(path_to_station_list)
    amy_file_list = amy_file_list[amy_file_list.columns[0]]

    # Initialize the df to hold paths of AMY files that could not be converted to an EPW.
    errors = pd.DataFrame(columns=['file', 'error'])

    num_files = len(amy_file_list)
    for idx, amy_file_path in enumerate(amy_file_list, start=1):
        # The NOAA ISD Lite AMY files are stored in directories named the same as the year they describe, so we
        # use that directory name to get the year
        amy_file_dir = os.path.dirname(amy_file_path)
        year = int(amy_file_dir.split(os.path.sep)[-1])
        next_year = year + 1

        # To get the WMO, we have to parse it out of the filename: it's the portion prior to the first hyphen
        wmo_index = int(os.path.basename(amy_file_path).split('-')[0])

        # Our NOAA ISD Lite input files are organized under inputs/NOAA_ISD_Lite_Raw/ in directories named after their
        # years, and the files are named identically (<WMO>_<###>_<Year>.gz), so we can get the path to the subsequent
        # year's file by switching directories and swapping the year in the file name.
        s = os.path.sep
        amy_subsequent_year_file_path = amy_file_path.replace(s + str(year) + s, s + str(next_year) + s)\
                                                     .replace(f'-{year}.gz', f'-{next_year}.gz')
        try:
            amy_epw_file_path = diyepw.create_amy_epw_file(
                wmo_index=wmo_index,
                year=year,
                max_records_to_impute=max_records_to_impute,
                max_records_to_interpolate=max_records_to_interpolate,
                amy_epw_dir=output_path,
                amy_files=(amy_file_path, amy_subsequent_year_file_path),
                allow_downloads=True,
            )

            click.echo(f"Success! {os.path.basename(amy_file_path)} => {os.path.basename(amy_epw_file_path)} ({idx} / {num_files})")
        except Exception as e:
            errors = errors.append({"file": amy_file_path, "error": str(e)}, ignore_index=True)
            click.echo(f"\n*** Error! {amy_file_path} could not be processed, see {errors_path} for details ({idx} / {num_files})\n")

    click.echo("\nDone!")

    if not errors.empty:
        click.echo(f"{len(errors)} files encountered errors - see {errors_path} for more information")
        errors.to_csv(errors_path, mode='w', index=False)

    click.echo(f"{num_files - len(errors)} files successfully processed. EPWs were written to {output_path}.")