#!/bin/sh
# Will be executed as user "root".

pluginname=owntracks4lox
touch $LBPLOG/$pluginname/owntracks.log > /dev/null 2>&1

echo "UNINSTALL: Starting ot-recorder uninstall script" >> $LBPLOG/$pluginname/owntracks.log
ot_configfile = $LBPCONFIG/recorder/ot-recorder
cd ~

if [ -f $ot_configfile ]; then
	echo "<INFO> Stop and disable ot-recorder service"
	systemctl stop ot-recorder
	systemctl disable ot-recorder

	#echo "<INFO> Create temporary folders for upgrading"
	#mkdir -p /tmp/$1\_upgrade
	#mkdir -p /tmp/$1\_upgrade/ot-config
	#mkdir -p /tmp/$1\_upgrade/data

	#echo "<INFO> Backing up ot-recorder config file"
	#cp -p -v -r /etc/default/ot-recorder /tmp/$1\_upgrade/ot-config
	
	#echo "<INFO> Backing up data"
	#cp -p -v -r /var/spool/owntracks/recorder /tmp/$1\_upgrade/data

	echo "<INFO> Delete previous installation"
	rm -r /usr/local/sbin/ot-recorder
	rm -r /usr/local/bin/ocat
	rm -r /var/spool/owntracks/recorder/htdocs/
	rm -r /etc/systemd/system/ot-recorder.service
else
	echo "<OK> Nothing to do"
fi

exit 0
