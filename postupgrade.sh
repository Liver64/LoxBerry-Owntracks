#!/bin/sh
# Will be executed as user "loxberry".

echo "<INFO> Copy back existing config files"
cp -p -v -r /tmp/$1\_upgrade/config/$3/* $5/config/plugins/$3/ 

#echo "<INFO> Copy back existing recorder config files"
#cp -p -v -r /tmp/$1\_upgrade/ot-config/ot-recorder /etc/default/ot-recorder 

echo "<INFO> Copy back existing log files"
cp -p -v -r /tmp/$1\_upgrade/log/$3/* $5/log/plugins/$3/ 

rm -r /tmp/$1\_upgrade

exit 0
