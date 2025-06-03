#!/bin/sh

mkdir -p build
cat metadata/openlibrary.py |sed -e 's/calibreweb\.//' > build/openlibrary.py
