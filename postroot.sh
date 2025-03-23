#!/bin/sh
# Will be executed as user "root".

if [ ! -d "REPLACELBPCONFIGDIR/recorder" ]; then
	echo "<INFO> Recorder Installation starts"
	source /etc/os-release
	
	if [ $VERSION_ID == "10" ]; then
		echo "<INFO> Recorder for Buster will be installed"
		curl https://raw.githubusercontent.com/owntracks/recorder/master/etc/repo.owntracks.org.gpg.key | sudo apt-key add -
		echo "deb  http://repo.owntracks.org/debian buster main" | sudo tee /etc/apt/sources.list.d/owntracks.list > /dev/null
		sudo apt-get update
		sudo apt-get install -y ot-recorder
	fi

	if [ $VERSION_ID == "11" ]; then
		echo "<INFO> Recorder for Bullseye will be installed"
		curl https://raw.githubusercontent.com/owntracks/recorder/master/etc/repo.owntracks.org.gpg.key | sudo apt-key add -
		echo "deb  http://repo.owntracks.org/debian bullseye main" | sudo tee /etc/apt/sources.list.d/owntracks.list > /dev/null
		sudo apt update
		sudo apt install -y -recorder
	fi
	if [ $VERSION_ID == "12" ]; then
		echo "<INFO> Recorder for Bookworm will be installed"
		curl --no-progress-meter https://raw.githubusercontent.com/owntracks/recorder/master/etc/repo.owntracks.org.gpg.key | sudo tee /etc/apt/trusted.gpg.d/owntracks.asc
		echo "deb  http://repo.owntracks.org/debian bookworm main" | sudo tee /etc/apt/sources.list.d/owntracks.list > /dev/null
		sudo apt update
		sudo apt install -y ot-recorder
	fi
	install -m444 /usr/share/doc/ot-recorder/ot-recorder.service /etc/systemd/system/ot-recorder.service
	
	#cp /REPLACELBPDATADIR/ot-recorder /etc/default
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
	
	echo "<INFO> Recorder successful installed by Plugin"
else
	echo "<INFO> Recorder already installed"
fi

exit 0
