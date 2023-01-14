#!/bin/bash
# 7z2bz2.sh
# Simple wrapper to convert xml.7z files to xml.bz2
# Useful to simplify multithreaded batch conversion, for instance:
# find * -name '*7z' -print | xargs -P8 -n 1 ./7z2bz2.sh
# CC-0, 2014

DUMP=$(echo $1 | sed 's/.7z//')
echo $DUMP
7z e -so $DUMP.7z $DUMP | bzip2 -c > $DUMP.bz2;
rm $1;
