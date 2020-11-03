import os
import argparse
import diyepw
import pandas as pd
from glob import iglob

output_dir_path = '../outputs/analyze_noaa_data_output'

parser = argparse.ArgumentParser(
    description=f"""
        Perform an analysis of a set of NOAA ISA Lite files, determining which are suitable for conversion to AMY
        EPW files using this project's create_amy_epw_files.py script.
    """
)
parser.add_argument('--max-missing-rows',
                    default=700,
                    type=int,
                    help='ISD files with more than this number of missing rows will be excluded from the output')
parser.add_argument('--max-consecutive-missing-rows',
                    default=48,
                    type=int,
                    help='ISD files with more than this number of consecutive missing rows will be excluded from the output')
parser.add_argument('--inputs',
                    default='../inputs/NOAA_ISD_Lite_Raw/**/*.gz',
                    type=str,
                    help='A glob (see https://docs.python.org/3/library/glob.html, basically a path string that supports'
                         'the * wildcard character) that will be searched for NOAA ISD Lite files, which may optionally'
                         'be compressed. The files must be named according to the format "<WMO Index>-<WBAN>-<Year>".'
                         'By default, all .gz files under inputs/NOAA_ISD_Lite_Raw/ will be included.'
                    )
args = parser.parse_args()

# Make a directory to store results if it doesn't already exist.
if not os.path.exists(output_dir_path):
    os.makedirs(output_dir_path)

analysis_results = diyepw.analyze_noaa_isd_lite_files(
    iglob('../inputs/NOAA_ISD_Lite_Raw/**/7*'),
    max_missing_rows=args.max_missing_rows,
    max_consecutive_missing_rows=args.max_consecutive_missing_rows
)

# Write the dataframes to CSVs for the output files.
num_files_with_too_many_rows_missing = len(analysis_results['too_many_total_rows_missing'])
if num_files_with_too_many_rows_missing > 0:
    path = os.path.join(output_dir_path, 'missing_total_entries_high.csv')
    print(
        num_files_with_too_many_rows_missing,
        "records excluded because they were missing more than", args.max_missing_rows,
        "rows. Information about these files will be written to", path
    )
    pd.DataFrame(analysis_results['too_many_total_rows_missing']).to_csv(path, index=False)

num_files_with_too_many_consec_rows_missing = len(analysis_results['too_many_consecutive_rows_missing'])
if num_files_with_too_many_consec_rows_missing > 0:
    path = os.path.join(output_dir_path, 'missing_consec_entries_high.csv')
    print(
        num_files_with_too_many_consec_rows_missing,
        "records excluded because they were missing more than", args.max_consecutive_missing_rows,
        "consecutive rows. Information about these files will be written to", path
    )
    pd.DataFrame(analysis_results['too_many_consecutive_rows_missing']).to_csv(path, index=False)

num_good_files = len(analysis_results['good'])
if num_good_files > 0:
    path = os.path.join(output_dir_path, 'files_to_convert.csv')
    print(
        num_good_files,
        "records are complete enough to be processed. Information about these files will be written to", path
    )
    pd.DataFrame(analysis_results['good']).to_csv(path, index=False)

print('Done! {count} files processed.'.format(count=sum([
    num_good_files,
    num_files_with_too_many_consec_rows_missing,
    num_files_with_too_many_rows_missing
])))