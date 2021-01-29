data/tmy_epw_files/
--------------------------
When TMY EPW files (EPWs containing meteorology based on a typical meteorological year) 
are downloaded in get_tmy_epw_file(), they are stored here by default. If you 
want to force a file to be downloaded again instead of the copy here being used, you 
can delete the copy of the file from this directory, or use the force_update argument 
of get_noaa_isd_lite_file().