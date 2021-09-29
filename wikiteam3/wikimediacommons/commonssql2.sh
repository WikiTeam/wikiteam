#!/bin/bash

source /home/emijrp/commons-archive/bin/activate
time python /home/emijrp/commons-archive/commonssql.py $1
deactivate
