#!/bin/sh
# Will be executed as user "root".

pluginname=owntracks4lox
touch $LBPLOG/$pluginname/owntracks.log > /dev/null 2>&1

echo "INSTALL: Starting ot-recorder uninstall script" >> $LBPLOG/$pluginname/owntracks.log
cd ~

echo "<INFO> Stop and disable ot-recorder service"
systemctl stop ot-recorder
systemctl disable ot-recorder

echo "<INFO> Create temporary folders for upgrading"
mkdir -p /tmp/$1\_upgrade
mkdir -p /tmp/$1\_upgrade/config

echo "<INFO> Backing up ot-recorder config file"
cp -p -v -r /etc/default/ot-recorder /tmp/$1\_upgrade/ot-config

echo "<INFO> Delete previous installation"
rm -r /src
rm -r /usr/local/sbin/ot-recorder
rm -r /usr/local/bin/ocat
rm -r /var/spool/owntracks/recorder/htdocs/
rm -r /etc/systemd/system/ot-recorder.service

# Exit with Status 0
exit 0
