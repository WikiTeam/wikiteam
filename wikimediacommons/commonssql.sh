#!/bin/bash

#virtualenv -p python commons-archive
#cd commons-archive
#source bin/activate
#pip install mysql-python
#deactivate
#cd ..
#sh commons-archive/commonssql.sh

for year in $(seq 2004 2016)
do
    jsub -N commonssql -mem 5000m /bin/bash /home/emijrp/commons-archive/commonssql2.sh $year
done
