#!/bin/sh
# Will be executed as user "root".

pluginname=owntracks4lox
touch $LBPLOG/$pluginname/owntracks.log > /dev/null 2>&1

echo "INSTALL: Starting ot-recorder install script" >> $LBPLOG/$pluginname/owntracks.log

$ot_configfile = $LBPCONFIG/recorder/ot-recorder
#PCONFIG=$LBPCONFIG/$PDIR

#if [ ! -f $ot_configfile ]; then
	cd ~
	mkdir /src
	cd /src
	echo "<INFO> Clone Repository"
	git clone https://github.com/owntracks/recorder.git
	cd ./recorder
	cp -av config.mk.in config.mk
	
	echo "<INFO> Installation started"
	make
	make install
	sleep 5
	
	echo "<INFO> Create symlinks and change permissions"
	mkdir -p REPLACELBPCONFIGDIR/recorder
	chmod 777 /etc/default/ot-recorder
	ln -s /etc/default/ot-recorder REPLACELBPCONFIGDIR/recorder/ot-recorder
	ln -s /var/spool/owntracks/recorder/store REPLACELBPDATADIR/recorder
		
	echo "<INFO> Copy back existing config files"
	cp -p -v -r /tmp/$1\_upgrade/ot-config/$3/* /etc/default/ot-recorder
	
	echo "<INFO> Remove temporary folders"
	rm -r /tmp/$1\_upgrade
	
	echo "<INFO> Start Service"
	systemctl enable ot-recorder
	systemctl start ot-recorder
	echo "<OK> Installation of ot-recorder completed"
	echo "<OK> ot-recorder service started and enabled"
	
#fi


# Exit with Status 0
exit 0
