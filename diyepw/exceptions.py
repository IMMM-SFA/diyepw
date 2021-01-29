
class DownloadNotAllowedError(Exception):
    """
    To be raised in situations where downloading a file would be necessary in order for correct
    functionality, but the caller has not given permission for file downloads to take place
    """
    pass