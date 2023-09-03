#!/bin/sh
# Will be executed as user "root".

if [ ! -d "REPLACELBPCONFIGDIR/recorder" ]; then
	echo "<INFO> Recorder Installation starts"
	
	curl https://raw.githubusercontent.com/owntracks/recorder/master/etc/repo.owntracks.org.gpg.key | sudo apt-key add -
	echo "deb  http://repo.owntracks.org/debian bullseye main" | sudo tee /etc/apt/sources.list.d/owntracks.list > /dev/null
	sudo apt update
	sudo apt install ot-recorder
	
	install -m444 /usr/share/doc/ot-recorder/ot-recorder.service /etc/systemd/system/ot-recorder.service
	
	chown loxberry /etc/default/ot-recorder
	
	systemctl enable ot-recorder
	systemctl start ot-recorder
	
	if [ ! -f REPLACELBPCONFIGDIR/recorder/ot-recorder ]; then
		mkdir REPLACELBPCONFIGDIR/recorder
		ln -s /etc/default/ot-recorder REPLACELBPCONFIGDIR/recorder
	fi
	
	if [ ! -d REPLACELBPDATADIR/recorder ]; then
		mkdir REPLACELBPDATADIR/recorder
		ln -s /var/spool/owntracks/recorder/store REPLACELBPDATADIR/recorder
	fi
	
	echo "<INFO> Recorder successful installed"
else
	echo "<INFO> Recorder already installed"
fi

exit 0
