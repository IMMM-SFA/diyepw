import logging as _logging
import os as _os
import sys as _sys
from datetime import datetime as _dt

_LOG_LEVEL = _logging.INFO

this_dir = _os.path.dirname(_os.path.realpath(__file__))

_log_path = _os.path.join(this_dir, '..', 'log', str(_dt.now()).replace(' ', '_') +'.log')
_file_handler = _logging.FileHandler(_log_path)
_file_handler.setFormatter(_logging.Formatter("%(asctime)s [diyepw.%(levelname)s] %(message)s"))
_file_handler.setLevel(_LOG_LEVEL)

_stdout_handler = _logging.StreamHandler(_sys.stdout)
_stdout_handler.setFormatter(_logging.Formatter("%(asctime)s %(message)s"))
_stdout_handler.setLevel(_LOG_LEVEL)

_logger = _logging.Logger('diyepw')
_logger.addHandler(_stdout_handler)
_logger.addHandler(_file_handler)