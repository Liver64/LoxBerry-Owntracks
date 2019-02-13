#!/bin/sh

# pluginname=$(basename $0 .sh)
pluginname=owntracks4lox
#touch $LBPLOG/$pluginname/owntracks.log > /dev/null 2>&1

#echo "DAEMON: Starting Owntracks recorder script" >> $LBPLOG/$pluginname/owntracks.log
#$ot_configfile = $PCONFIG"/recorder/ot-recorder"
#PCONFIG=$LBPCONFIG/$PDIR

#if [ ! -f $ot_configfile ]; then
	rm /etc/systemd/system/ot-recorder.service
	rm /etc/default/ot-recorder
	cd ~
	mkdir /src
	cd /src
	git clone https://github.com/owntracks/recorder.git
	mkdir files
	cp -av /opt/loxberry/bin/plugins/owntracks4lox/install/. /src/files/
	#cp -av /tmp/uploads/$1/bin/plugins/$2/install/ /src/files/
	cd ./recorder
	#cp -av config.mk.in config.mk
	cp -av /src/files/config.mk.in config.mk
	cp -av /src/files/ot-recorder.bin /etc/default/ot-recorder
	cp -av /src/files/ot-recorder.bin /etc/systemd/system/ot-recorder.service
	cp -av /src/files/ot-recorder.tmp /etc/ot-recorder.default
	sudo chown -R loxberry:loxberry /opt/loxberry/config/plugins/owntracks4lox
	#cd /src/recorder
	make
	sudo make install
	#rm -r /opt/loxberry/config/plugins/owntracks4lox/tmp
	#install -m444 /src/recorder/etc/ot-recorder.service /etc/systemd/system/ot-recorder.service
	#sudo chown -R loxberry:loxberry /opt/loxberry/config/plugins/owntracks4lox
	#sudo chown -R loxberry:loxberry /opt/loxberry/data/plugins/owntracks4lox
	systemctl enable ot-recorder
	systemctl start ot-recorder
#fi


# Exit with Status 0
exit 0


cp -av /src/files/ot-recorder.bin /opt/loxberry/config/plugins/owntracks4lox/recorder/ot-recorder
sudo chown -R root:root /opt/loxberry/config/plugins/owntracks4lox/recorder
sudo chmod 777 /opt/loxberry/config/plugins/owntracks4lox/recorder/ot-recorder