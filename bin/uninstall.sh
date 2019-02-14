#!/bin/sh
# Will be executed as user "root".

pluginname=owntracks4lox
touch $LBPLOG/$pluginname/owntracks.log > /dev/null 2>&1

echo "UNINSTALL: Starting ot-recorder uninstall script" >> $LBPLOG/$pluginname/owntracks.log
ot_configfile = $LBPCONFIG/recorder/ot-recorder
cd ~

systemctl stop ot-recorder
systemctl disable ot-recorder
rm -r /usr/local/sbin/ot-recorder
rm -r /usr/local/bin/ocat
rm -r /var/spool/owntracks/recorder/htdocs/
rm -r /var/spool/owntracks/recorder/recorder/
rm -r /etc/systemd/system/ot-recorder.service
rm -r /etc/default/ot-recorder
rm -r $LBPCONFIG/recorder/
rm -r $LBPDATA/recorder/

# Exit with Status 0
exit 0
