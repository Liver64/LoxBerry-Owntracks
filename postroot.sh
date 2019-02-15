#!/bin/sh
# Will be executed as user "root".

if [ ! -d "REPLACELBPCONFIGDIR/recorder" ]; then
	curl http://repo.owntracks.org/repo.owntracks.org.gpg.key | sudo apt-key add -
	echo "deb  http://repo.owntracks.org/debian stretch main" | sudo tee /etc/apt/sources.list.d/owntracks.list > /dev/null
	apt-get -y update
	apt-get -y install ot-recorder
	install -m444 /usr/share/doc/ot-recorder/ot-recorder.service /etc/systemd/system/ot-recorder.service
	systemctl enable ot-recorder
	systemctl start ot-recorder
	sleep 10
	chmod 777 /etc/default/ot-recorder
	
	if [ ! -f REPLACELBPCONFIGDIR/recorder/ot-recorder ]; then
		mkdir REPLACELBPCONFIGDIR/recorder
		ln -s /etc/default/ot-recorder REPLACELBPCONFIGDIR/recorder
	fi
	
	if [ ! -d REPLACELBPDATADIR/recorder ]; then
		mkdir REPLACELBPDATADIR/recorder
		ln -s /var/spool/owntracks/recorder/store REPLACELBPDATADIR/recorder
	fi
	
	echo "<INFO> Recorder installed"
else
	echo "<INFO> Recorder already installed"
fi

exit 0
