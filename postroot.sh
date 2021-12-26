#!/bin/sh
# Will be executed as user "root".

if [ ! -d "REPLACELBPCONFIGDIR/recorder" ]; then
#if [  -d "REPLACELBPCONFIGDIR/recorder" ]; then
	echo "<INFO> Recorder Installation starts"
	
	wget http://repo.owntracks.org/repo.owntracks.org.gpg.key
	apt-key add repo.owntracks.org.gpg.key
	echo "deb  http://repo.owntracks.org/debian buster main" > /etc/apt/sources.list.d/owntracks.list
	curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | sudo apt-key add -
	
	#curl https://raw.githubusercontent.com/owntracks/recorder/master/etc/repo.owntracks.org.gpg.key | sudo apt-key add -
	#echo "deb  http://repo.owntracks.org/debian buster main" | sudo tee /etc/apt/sources.list.d/owntracks.list > /dev/null
	#apt-get -y update
	#apt-get -y install ot-recorder
	#install -m444 /usr/share/doc/ot-recorder/ot-recorder.service /etc/systemd/system/ot-recorder.service
	
	# Update repro with valid links
	sudo apt update -y
	apt-get -y update
	
	mkdir /usr/share/owntracks
	ln -s /usr/local/bin/ocat /usr/bin/ocat
	ln -s /usr/local/sbin/ot-recorder /usr/sbin/ot-recorder
	#apt-get -y install ot-recorder
	#install -m444 /usr/share/doc/ot-recorder/ot-recorder.service /etc/systemd/system/ot-recorder.service
	
	systemctl enable ot-recorder
	service ot-recorder --initialize
	systemctl start ot-recorder
	sleep 20
	#chmod 777 /etc/default/ot-recorder
	
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
