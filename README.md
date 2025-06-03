This is a metadata plugin written for Calibre-web. It queries the OpenLibrary API. There are 
often books that standard google or amazon metadata doesn't include book covers or metadata or a book is just not found. This provides
another option to locate book metadata.

## Installation
1. ./build.sh
2. copy the file build/openlibrary.py into the python calibreweb module install directory (e.g. /opt/venv/lib/python3.11/site-packages/calibreweb/cps/metadata_providers). See https://stackoverflow.com/questions/247770/how-to-retrieve-a-modules-path for how to locate the install path for the module on your system.
3. restart the calibre-web service `sudo systemctl restart cps`
