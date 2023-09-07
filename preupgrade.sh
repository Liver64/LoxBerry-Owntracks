#!/bin/sh
# Will be executed as user "loxberry".

# To use important variables from command line use the following code:
COMMAND=$0    # Zero argument is shell command
PTEMPDIR=$1   # First argument is temp folder during install
PSHNAME=$2    # Second argument is Plugin-Name for scipts etc.
PDIR=$3       # Third argument is Plugin installation folder
PVERSION=$4   # Forth argument is Plugin version
LBHOMEDIR=$5  # Comes from /etc/environment now. Fifth argument is
              # Base folder of LoxBerry

# Combine them with /etc/environment
PCGI=$LBPCGI/$PDIR
PHTML=$LBPHTML/$PDIR
PTEMPL=$LBPTEMPL/$PDIR
PDATA=$LBPDATA/$PDIR
PLOG=$LBPLOG/$PDIR # Note! This is stored on a Ramdisk now!
PCONFIG=$LBPCONFIG/$PDIR
PSBIN=$LBPSBIN/$PDIR
PBIN=$LBPBIN/$PDIR


DIR=$LBPDATA/$PDIR/backup

echo "<INFO> Creating temporary folders for upgrading"
mkdir -p /tmp/$1\_upgrade
mkdir -p /tmp/$1\_upgrade/config
mkdir -p /tmp/$1\_upgrade/webfrontend
mkdir -p /tmp/$1\_upgrade/webfrontend/htmlauth
#mkdir -p /tmp/$1\_upgrade/webfrontend/htmlauth/files
mkdir -p /tmp/$1\_upgrade/log

echo "<INFO> Backing up existing config files"
cp -p -v -r $5/config/plugins/$3/ /tmp/$1\_upgrade/config

echo "<INFO> Backing up existing log files"
cp -p -v -r $5/log/plugins/$3/ /tmp/$1\_upgrade/log

echo "<INFO> Backing up existing User App files"
cp -p -v -r $5/webfrontend/htmlauth/plugins/$3/ /tmp/$1\_upgrade/webfrontend/htmlauth

exit 0
