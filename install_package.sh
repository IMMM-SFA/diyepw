#!/bin/bash

##
# install_package.sh - Installs the DIYEPW Python package
# Get the directory containing this script (credit to https://stackoverflow.com/a/246128)
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"


pip install -e "$DIR"/lib/diyepw