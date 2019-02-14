#!/bin/sh
# Will be executed as user "root".

pluginname=owntracks4lox
touch $LBPLOG/$pluginname/owntracks.log > /dev/null 2>&1

echo "INSTALL: Starting ot-recorder install script" >> $LBPLOG/$pluginname/owntracks.log

ot_configfile = $LBPCONFIG/recorder/ot-recorder
#PCONFIG=$LBPCONFIG/$PDIR

#if [ ! -f $ot_configfile ]; then
	cd ~
	mkdir /src
	cd /src
	echo "<INFO> Clone Repository"
	git clone https://github.com/owntracks/recorder.git
	cd ./recorder
	cp -av config.mk.in config.mk
	
	echo "<INFO> Start Installation..."
	make
	make install
	sleep 10
	install --mode 0644 etc/ot-recorder.service /etc/systemd/system/ot-recorder.service
	
	echo "<INFO> Create symlinks and change permissions"
	mkdir -p REPLACELBPCONFIGDIR/recorder
	chmod 777 /etc/default/ot-recorder
	ln -s /etc/default/ot-recorder REPLACELBPCONFIGDIR/recorder/ot-recorder
	ln -s /var/spool/owntracks/recorder/store REPLACELBPDATADIR/recorder
		
	echo "<INFO> Copy back existing config files"
	cp -p -v -r /tmp/$1\_upgrade/ot-config/ot-recorder /etc/default/ot-recorder
	
	echo "<INFO> Remove temporary folders"
	rm -r /tmp/$1\_upgrade
	
	echo "<INFO> Start Service"
	systemctl enable ot-recorder
	systemctl start ot-recorder
	echo "<INFO> Installation of ot-recorder completed"
	cd ~
	rm -r /src
	echo "<INFO> Temp folder deleted"
	echo "<OK> ot-recorder service enabled and started"
#else
	echo "<INFO> ot-recorder already installed"
#fi



# Exit with Status 0
exit 0
