import logging
import os
import sys
from datetime import datetime

_LOG_LEVEL = logging.INFO

this_dir = os.path.dirname(os.path.realpath(__file__))

_log_path = os.path.join(this_dir, '..', 'log', str(datetime.now()).replace(' ', '_') +'.log')
_file_handler = logging.FileHandler(_log_path)
_file_handler.setFormatter(logging.Formatter("%(asctime)s [diyepw.%(levelname)s] %(message)s"))
_file_handler.setLevel(_LOG_LEVEL)

_stdout_handler = logging.StreamHandler(sys.stdout)
_stdout_handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
_stdout_handler.setLevel(_LOG_LEVEL)

_logger = logging.Logger('diyepw')
_logger.addHandler(_stdout_handler)
_logger.addHandler(_file_handler)