#!/bin/sh
#
# LoxBerry OwnTracks plugin
# Upgrade restore script
#
# Runs as user "loxberry" after the new plugin files have been installed and
# before postroot.sh is executed.
#

set -u

PTEMPDIR=$1
PSHNAME=$2
PDIR=$3
PVERSION=$4
LBHOMEDIR=$5

BACKUP_DIR="/tmp/${PTEMPDIR}_upgrade"
CONFIG_DIR="${LBHOMEDIR}/config/plugins/${PDIR}"
DATA_DIR="${LBHOMEDIR}/data/plugins/${PDIR}"
HTMLAUTH_DIR="${LBHOMEDIR}/webfrontend/htmlauth/plugins/${PDIR}"

if [ ! -d "$BACKUP_DIR" ]; then
    echo "<WARNING> No OwnTracks upgrade backup directory was found."
    exit 1
fi

echo "<INFO> Restoring OwnTracks plugin configuration."
if ! mkdir -p "$CONFIG_DIR"; then
    echo "<ERROR> Could not create $CONFIG_DIR."
    exit 2
fi

for SRC in "$BACKUP_DIR/config"/*; do
    [ -f "$SRC" ] || continue
    if ! cp -p "$SRC" "$CONFIG_DIR/"; then
        echo "<ERROR> Could not restore $SRC."
        exit 2
    fi
done

# Restore only generated app files. Packaged template files from the new release
# remain untouched.
if [ -d "$BACKUP_DIR/user_config_files" ]; then
    echo "<INFO> Restoring generated OwnTracks app configuration files."
    if ! mkdir -p "$DATA_DIR/user_config_files"; then
        echo "<ERROR> Could not create $DATA_DIR/user_config_files."
        exit 2
    fi

    for SRC in "$BACKUP_DIR/user_config_files"/*.otrc; do
        [ -f "$SRC" ] || continue
        if ! cp -p "$SRC" "$DATA_DIR/user_config_files/"; then
            echo "<ERROR> Could not restore $SRC."
            exit 2
        fi
    done
fi

# Restore legacy files only when real content was backed up. They are left in
# the old location so the plugin's existing migration routine can consume them.
if [ -d "$BACKUP_DIR/legacy-htmlauth/files" ] && \
   [ -n "$(find "$BACKUP_DIR/legacy-htmlauth/files" -mindepth 1 -print -quit 2>/dev/null)" ]
then
    echo "<INFO> Restoring legacy OwnTracks app files for migration."
    if ! mkdir -p "$HTMLAUTH_DIR/files" || \
       ! cp -p -R "$BACKUP_DIR/legacy-htmlauth/files"/. "$HTMLAUTH_DIR/files"/
    then
        echo "<ERROR> Could not restore legacy OwnTracks app files."
        exit 2
    fi
fi

rm -rf "$BACKUP_DIR"

echo "<OK> OwnTracks upgrade data restored successfully."
exit 0
