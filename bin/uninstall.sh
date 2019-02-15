#!/bin/sh
# Will be executed as user "root".

systemctl stop ot-recorder
systemctl disable ot-recorder
rm -r /usr/sbin/ot-recorder
rm -r /usr/bin/ocat
rm -r /var/spool/owntracks/
rm -r /etc/systemd/system/ot-recorder.service
rm -r /etc/default/ot-recorder
rm -r /usr/share/owntracks/
rm -r REPLACELBPCONFIGDIR/recorder/
rm -r REPLACELBPDATADIR/recorder/

# Exit with Status 0
exit 0
