#!/bin/sh
# Will be executed as user "loxberry".

echo "<INFO> Creating temporary folders for upgrading"
mkdir -p /tmp/$1\_upgrade
mkdir -p /tmp/$1\_upgrade/config
mkdir -p /tmp/$1\_upgrade/webfrontend
mkdir -p /tmp/$1\_upgrade/webfrontend/htmlauth
mkdir -p /tmp/$1\_upgrade/log

echo "<INFO> Backing up existing config files"
cp -p -v -r $5/config/plugins/$3/ /tmp/$1\_upgrade/config

#echo "<INFO> Backing up ot-recorder config file"
#cp -p -v -r /etc/default/ot-recorder /tmp/$1\_upgrade/ot-config/ot-recorder

echo "<INFO> Backing up existing log files"
cp -p -v -r $5/log/plugins/$3/ /tmp/$1\_upgrade/log

echo "<INFO> Backing up existing User App files"
cp -p -v -r $5/webfrontend/htmlauth/plugins/$3/files /tmp/$1\_upgrade/webfrontend/htmlauth

exit 0
