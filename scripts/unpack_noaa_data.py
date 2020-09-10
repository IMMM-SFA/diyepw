# Run before analyze_noaa_data.py

import glob
import gzip
import shutil

zipfiles = '../inputs/NOAA_ISD_Lite_Raw/*/*.gz'

filelist = glob.glob(zipfiles, recursive=True)

for gzfile in filelist:
    # Grab the file name
    gzfile_string = gzfile.split("/")[-1]
    filename_string = gzfile_string[0:-3]
    # Unpack gz file and send to csv
    with gzip.open(gzfile, 'rb') as f_in:
        with open(str('../outputs/NOAA_AMY/'+filename_string), 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
