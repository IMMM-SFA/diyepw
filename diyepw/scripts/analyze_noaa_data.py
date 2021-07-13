import click
import diyepw
from glob import iglob
import os
import pandas as pd


@click.command()
@click.option(
    '--max-missing-rows',
    default=700,
    show_default=True,
    type=int,
    help='ISD files with more than this number of missing rows will be excluded from the output'
)
@click.option(
    '--max-consecutive-missing-rows',
    default=48,
    show_default=True,
    type=int,
    help='ISD files with more than this number of consecutive missing rows will be excluded from the output'
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
    'input_path',
    default='.',
    type=click.Path(
        file_okay=False,
        dir_okay=True,
        readable=True,
        resolve_path=True,
    ),
)
def analyze_noaa_data(
    max_missing_rows,
    max_consecutive_missing_rows,
    output_path,
    input_path,
):
    """Perform an analysis of a set of NOAA ISA Lite files, determining which are suitable for conversion to
       AMY EPW files. Any ISD Lite files in INPUT_PATH or any of its subdirectories will be processed. The files
       must be named according to the format '<WMO Index>-<WBAN>-<Year>' and must end with '.gz', '.csv', or '.zip'."""

    # Make a directory to store results if it doesn't already exist.
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    # Recursively search for all files under the passed path, excluding directories
    input_files = [file for file in iglob(input_path + '/**/*', recursive=True) if not os.path.isdir(file)]

    try:
        analysis_results = diyepw.analyze_noaa_isd_lite_files(
            input_files,
            max_missing_rows=max_missing_rows,
            max_consecutive_missing_rows=max_consecutive_missing_rows,
        )
    except:
        click.echo("Unable to read input files, aborting...")
        raise click.Abort

    # Write the dataframes to CSVs for the output files.
    num_files_with_too_many_rows_missing = len(analysis_results['too_many_total_rows_missing'])
    if num_files_with_too_many_rows_missing > 0:
        path = os.path.join(output_path, 'missing_total_entries_high.csv')
        path = os.path.abspath(path)  # Change to absolute path for readability
        click.echo(f"""{num_files_with_too_many_rows_missing}
                       records excluded because they were missing more than {max_missing_rows}
                       rows. Information about these files will be written to {path}.""")
        pd.DataFrame(analysis_results['too_many_total_rows_missing']).to_csv(path, index=False)

    num_files_with_too_many_consec_rows_missing = len(analysis_results['too_many_consecutive_rows_missing'])
    if num_files_with_too_many_consec_rows_missing > 0:
        path = os.path.join(output_path, 'missing_consec_entries_high.csv')
        path = os.path.abspath(path)  # Change to absolute path for readability
        click.echo(f"""{num_files_with_too_many_consec_rows_missing}
                       records excluded because they were missing more than {max_consecutive_missing_rows}
                       consecutive rows. Information about these files will be written to {path}.""")
        pd.DataFrame(analysis_results['too_many_consecutive_rows_missing']).to_csv(path, index=False)

    num_good_files = len(analysis_results['good'])
    if num_good_files > 0:
        path = os.path.join(output_path, 'files_to_convert.csv')
        path = os.path.abspath(path)  # Change to absolute path for readability
        click.echo(f"""{num_good_files} records are complete enough to be processed.
                       Information about these files will be written to {path}.""")
        pd.DataFrame(analysis_results['good']).to_csv(path, index=False)

    click.echo('Done! {count} files processed.'.format(count=sum([
        num_good_files,
        num_files_with_too_many_consec_rows_missing,
        num_files_with_too_many_rows_missing
    ])))
