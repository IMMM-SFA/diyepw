import logging
import os
import sys
import pkg_resources
from datetime import datetime

_LOG_LEVEL = logging.INFO

log_dir = pkg_resources.resource_filename("diyepw", "log")
if not os.path.exists(log_dir): # pragma: no cover
    os.mkdir(log_dir)

_log_path = os.path.join(log_dir, str(datetime.now()).replace(' ', '_').replace(':', '_') +'.log')
_file_handler = logging.FileHandler(_log_path)
_file_handler.setFormatter(logging.Formatter("%(asctime)s [diyepw.%(levelname)s] %(message)s"))
_file_handler.setLevel(_LOG_LEVEL)

_stdout_handler = logging.StreamHandler(sys.stdout)
_stdout_handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
_stdout_handler.setLevel(_LOG_LEVEL)

_logger = logging.Logger('diyepw')
_logger.addHandler(_stdout_handler)
_logger.addHandler(_file_handler)
