#!/bin/sh
#
# LoxBerry OwnTracks plugin
# Upgrade backup script
#
# Runs as user "loxberry" before LoxBerry removes the old plugin files.
# Preserve only user-generated/persistent state so packaged defaults from a
# newer release are not overwritten with old copies during the restore.
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

copy_file_if_present()
{
    SRC=$1
    DST_DIR=$2

    if [ -f "$SRC" ]; then
        mkdir -p "$DST_DIR" || return 1
        cp -p "$SRC" "$DST_DIR/" || return 1
    fi

    return 0
}

echo "<INFO> Preparing temporary OwnTracks upgrade backup."

rm -rf "$BACKUP_DIR"
if ! mkdir -p \
    "$BACKUP_DIR/config" \
    "$BACKUP_DIR/user_config_files" \
    "$BACKUP_DIR/legacy-htmlauth/files"
then
    echo "<ERROR> Could not create the temporary upgrade backup directory $BACKUP_DIR."
    exit 2
fi

# Persistent plugin settings.
echo "<INFO> Backing up OwnTracks plugin configuration."
if ! copy_file_if_present "$CONFIG_DIR/owntracks.cfg" "$BACKUP_DIR/config"; then
    echo "<ERROR> Could not back up owntracks.cfg."
    exit 2
fi

# Generated Recorder configuration. The package may replace
# /etc/default/ot-recorder during an upgrade; postroot.sh re-applies this copy.
if ! copy_file_if_present "$CONFIG_DIR/ot-recorder" "$BACKUP_DIR/config"; then
    echo "<ERROR> Could not back up the Recorder configuration."
    exit 2
fi

# Generated OwnTracks mobile-app configuration files. Do not back up the
# packaged config_template.otrc; the new release must keep its current template.
if [ -d "$DATA_DIR/user_config_files" ]; then
    echo "<INFO> Backing up generated OwnTracks app configuration files."
    for SRC in "$DATA_DIR/user_config_files"/*.otrc; do
        [ -f "$SRC" ] || continue
        [ "$(basename "$SRC")" = "config_template.otrc" ] && continue

        if ! cp -p "$SRC" "$BACKUP_DIR/user_config_files/"; then
            echo "<ERROR> Could not back up $SRC."
            exit 2
        fi
    done
fi

# Very old OwnTracks versions stored generated app files below htmlauth/files.
# Preserve those files as a migration safety net for direct upgrades.
if [ -d "$HTMLAUTH_DIR/files" ]; then
    echo "<INFO> Backing up legacy OwnTracks app files."
    if ! cp -p -R "$HTMLAUTH_DIR/files"/. "$BACKUP_DIR/legacy-htmlauth/files"/; then
        echo "<ERROR> Could not back up legacy OwnTracks app files."
        exit 2
    fi
fi

echo "<OK> OwnTracks upgrade backup completed."
exit 0
