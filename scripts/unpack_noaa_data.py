# Run before analyze_noaa_data.py

import glob
import gzip
import shutil
import os
import argparse

zipfiles_base_dir = os.path.join('..', 'inputs', 'NOAA_ISD_Lite_Raw')
zipfiles = os.path.join(zipfiles_base_dir, '*', '*.gz')
filelist = glob.glob(zipfiles, recursive=True)
output_dir = os.path.join('..', 'outputs', 'NOAA_AMY')

# We don't really take advantage of argparse, since there are no arguments to this scripts, but by having
# this we support calling this script with the --help flag, making it behave consistently with other
# scripts in this project
parser = argparse.ArgumentParser(
    description=f"""
        Unpack the compressed files in {zipfiles_base_dir} and put the decompressed files in {output_dir} 
    """
)
args = parser.parse_args()  # This call is required for --help support

# Create the output directory if it doesn't already exist
if not os.path.exists(output_dir):
    print("Creating outputs directory " + output_dir)
    os.mkdir(output_dir)

for gzfile in filelist:
    # Grab the file name
    gzfile_string = os.path.basename(gzfile)
    filename_string = os.path.splitext(gzfile_string)[0]  # Remove the extension from the file name
    # Unpack gz file and send to csv
    with gzip.open(gzfile, 'rb') as f_in:
        output_path = os.path.join(output_dir, filename_string)
        with open(output_path, 'wb') as f_out:
            print("Copying %s to %s" % (filename_string, output_path))
            shutil.copyfileobj(f_in, f_out)
