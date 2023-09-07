#!/bin/sh

# Bash script which is executed in case of an update (if this plugin is already
# installed on the system). This script is executed as very last step (*AFTER*
# postinstall) and can be for example used to save back or convert saved
# userfiles from /tmp back to the system. Use with caution and remember, that
# all systems may be different!
#
# Exit code must be 0 if executed successfull. 
# Exit code 1 gives a warning but continues installation.
# Exit code 2 cancels installation.
#
# Will be executed as user "loxberry".
#
# You can use all vars from /etc/environment in this script.
#
# We add 5 additional arguments when executing this script:
# command <TEMPFOLDER> <NAME> <FOLDER> <VERSION> <BASEFOLDER>
#
# For logging, print to STDOUT. You can use the following tags for showing
# different colorized information during plugin installation:
#
# <OK> This was ok!"
# <INFO> This is just for your information."
# <WARNING> This is a warning!"
# <ERROR> This is an error!"
# <FAIL> This is a fail!"

# To use important variables from command line use the following code:
COMMAND=$0    # Zero argument is shell command
PTEMPDIR=$1   # First argument is temp folder during install
PSHNAME=$2    # Second argument is Plugin-Name for scipts etc.
PDIR=$3       # Third argument is Plugin installation folder
PVERSION=$4   # Forth argument is Plugin version
LBHOMEDIR=$5  # Comes from /etc/environment now. Fifth argument is
              # Base folder of LoxBerry

echo "<INFO> Copy back existing config files"
cp -p -v -r /tmp/$1\_upgrade/config/$3/* $5/config/plugins/$3/ 

#echo "<INFO> Copy back existing recorder config files"
#cp -p -v -r /tmp/$1\_upgrade/ot-config/ot-recorder /etc/default/ot-recorder 

echo "<INFO> Copy back existing log files"
cp -p -v -r /tmp/$1\_upgrade/log/$3/* $5/log/plugins/$3/ 

mkdir -p $5/webfrontend/htmlauth/plugins/$3/files

echo "<INFO> Copy back existing User App files"
cp -p -v -r /tmp/$1\_upgrade/webfrontend/htmlauth/$3/files/* $5/webfrontend/htmlauth/plugins/$3/files/ 

rm -r /tmp/$1\_upgrade

exit 0
