#!/bin/sh
#
# LoxBerry OwnTracks plugin
# Root post-installation script
#
# This script runs after LoxBerry has installed the packages
# listed in dpkg/apt.
#

set -u

PACKAGE_NAME="ot-recorder"

SERVICE_NAME="ot-recorder.service"
SERVICE_TARGET="/etc/systemd/system/ot-recorder.service"
SERVICE_SOURCE="/usr/share/doc/ot-recorder/ot-recorder.service"

DEFAULT_FILE="/etc/default/ot-recorder"
STORE_DIR="/var/spool/owntracks/recorder/store"

PLUGIN_CONFIG_DIR="REPLACELBHOMEDIR/config/plugins/owntracks4lox/recorder"
PLUGIN_DATA_DIR="REPLACELBHOMEDIR/data/plugins/owntracks4lox/recorder"
PLUGIN_SAVED_CONFIG="REPLACELBHOMEDIR/config/plugins/owntracks4lox/ot-recorder"

CONFIG_LINK="${PLUGIN_CONFIG_DIR}/ot-recorder"
STORE_LINK="${PLUGIN_DATA_DIR}/store"

echo "<INFO> Configuring the OwnTracks Recorder installation."

#
# Verify that the package was installed by the LoxBerry installer.
#
if ! dpkg-query \
    -W \
    -f='${Status}' \
    "$PACKAGE_NAME" \
    2>/dev/null \
    | grep -q '^install ok installed$'
then
    echo "<ERROR> The package $PACKAGE_NAME is not installed."
    echo "<ERROR> Ensure that the file dpkg/apt contains the package name ot-recorder."
    exit 2
fi

#
# Verify required package files.
#
if [ ! -x /usr/sbin/ot-recorder ]; then
    echo "<ERROR> The OwnTracks Recorder executable /usr/sbin/ot-recorder is missing."
    exit 2
fi

if [ ! -f "$DEFAULT_FILE" ]; then
    echo "<ERROR> The OwnTracks configuration file $DEFAULT_FILE is missing."
    exit 2
fi

#
# Verify required system users.
#
if ! id owntracks >/dev/null 2>&1; then
    echo "<ERROR> The system user owntracks was not created by the package installation."
    exit 2
fi

if ! id loxberry >/dev/null 2>&1; then
    echo "<ERROR> The LoxBerry system user loxberry does not exist."
    exit 2
fi

echo "<INFO> Checking the OwnTracks systemd service."

# Current OwnTracks packages install the service unit directly into systemd.
# Older packages may only provide a copy below /usr/share/doc. Prefer an
# already installed unit and use the documentation copy only as a fallback.
if systemctl cat "$SERVICE_NAME" >/dev/null 2>&1; then
    echo "<INFO> Using the OwnTracks systemd service installed by the package."
elif [ -f "$SERVICE_SOURCE" ]; then
    echo "<INFO> Installing the OwnTracks systemd service supplied by the package."
    if ! install -o root -g root -m 0644 "$SERVICE_SOURCE" "$SERVICE_TARGET"; then
        echo "<ERROR> Could not install $SERVICE_SOURCE."
        exit 2
    fi
else
    echo "<WARNING> No OwnTracks systemd service was installed by the package."
    echo "<INFO> Creating a compatible OwnTracks systemd service."

    cat > "$SERVICE_TARGET" <<'EOF'
[Unit]
Description=OwnTracks Recorder
Wants=network-online.target
After=network-online.target

[Service]
Type=simple
User=owntracks
WorkingDirectory=/
ExecStartPre=/bin/sleep 3
ExecStart=/usr/sbin/ot-recorder

[Install]
WantedBy=multi-user.target
EOF

    if ! chown root:root "$SERVICE_TARGET"; then
        echo "<ERROR> Could not set the owner of $SERVICE_TARGET."
        exit 2
    fi

    if ! chmod 0644 "$SERVICE_TARGET"; then
        echo "<ERROR> Could not set the permissions of $SERVICE_TARGET."
        exit 2
    fi
fi

if ! systemctl daemon-reload; then
    echo "<ERROR> systemd could not reload its unit files."
    exit 2
fi

if ! systemctl cat "$SERVICE_NAME" >/dev/null 2>&1; then
    echo "<ERROR> The OwnTracks systemd service is unavailable."
    exit 2
fi

echo "<OK> The OwnTracks systemd service is available."

#
# On upgrades the LoxBerry pre/post-upgrade scripts restore the recorder
# configuration saved by the plugin. Re-apply it after a possible package
# upgrade so /etc/default/ot-recorder cannot silently fall back to package
# defaults. Fresh installations do not have this file yet.
#
if [ -f "$PLUGIN_SAVED_CONFIG" ]; then
    echo "<INFO> Restoring the saved OwnTracks Recorder configuration."

    if ! install \
        -o root \
        -g owntracks \
        -m 0640 \
        "$PLUGIN_SAVED_CONFIG" \
        "$DEFAULT_FILE"
    then
        echo "<ERROR> Could not restore the saved OwnTracks Recorder configuration."
        exit 2
    fi
fi

#
# The Recorder runs as user owntracks and must be able to read
# the configuration file.
#
echo "<INFO> Setting permissions for the OwnTracks configuration file."

if ! chown root:owntracks "$DEFAULT_FILE"; then
    echo "<ERROR> Could not set the owner of $DEFAULT_FILE."
    exit 2
fi

if ! chmod 0640 "$DEFAULT_FILE"; then
    echo "<ERROR> Could not set the permissions of $DEFAULT_FILE."
    exit 2
fi

#
# Ensure that the Recorder storage directory exists.
#
echo "<INFO> Preparing the OwnTracks storage directory."

if [ ! -d "$STORE_DIR" ]; then
    if ! install \
        -d \
        -o owntracks \
        -g owntracks \
        -m 0750 \
        "$STORE_DIR"
    then
        echo "<ERROR> Could not create the OwnTracks storage directory $STORE_DIR."
        exit 2
    fi
fi

if ! chown owntracks:owntracks "$STORE_DIR"; then
    echo "<ERROR> Could not set the owner of the OwnTracks storage directory $STORE_DIR."
    exit 2
fi

if ! chmod 0750 "$STORE_DIR"; then
    echo "<ERROR> Could not set the permissions of the OwnTracks storage directory $STORE_DIR."
    exit 2
fi

#
# Initialize the Recorder storage only when the LMDB structure is missing.
# Newer OwnTracks Debian packages restart the service from their package
# post-install script. Running --initialize concurrently with that service can
# fail even though an existing store is perfectly valid. Therefore an existing
# LMDB database is left untouched. For a fresh store, stop the service first,
# initialize it, and print the real Recorder error if initialization fails.
#
if [ -f "$STORE_DIR/ghash/data.mdb" ] || [ -f "$STORE_DIR/ghash/lock.mdb" ]; then
    echo "<OK> Existing OwnTracks Recorder storage detected; initialization is not required."
else
    echo "<INFO> Initializing the OwnTracks Recorder storage."

    if systemctl is-active --quiet "$SERVICE_NAME" 2>/dev/null; then
        echo "<INFO> Stopping the OwnTracks Recorder temporarily for initialization."
        if ! systemctl stop "$SERVICE_NAME"; then
            echo "<ERROR> The OwnTracks Recorder service could not be stopped for initialization."
            exit 2
        fi
    fi

    INIT_LOG=$(mktemp /tmp/owntracks-init.XXXXXX) || {
        echo "<ERROR> Could not create a temporary initialization log."
        exit 2
    }

    if /usr/sbin/ot-recorder --initialize >"$INIT_LOG" 2>&1; then
        rm -f "$INIT_LOG"
        echo "<OK> The OwnTracks Recorder storage is initialized."
    else
        echo "<ERROR> The OwnTracks Recorder storage could not be initialized."
        if [ -s "$INIT_LOG" ]; then
            sed 's/^/<ERROR> ot-recorder: /' "$INIT_LOG"
        fi
        rm -f "$INIT_LOG"
        exit 2
    fi
fi

#
# Create plugin directories owned by the LoxBerry user.
# This prevents permission errors during future plugin upgrades.
#
echo "<INFO> Creating the LoxBerry plugin directories."

if ! install \
    -d \
    -o loxberry \
    -g loxberry \
    -m 0755 \
    "$PLUGIN_CONFIG_DIR"
then
    echo "<ERROR> Could not create the plugin configuration directory $PLUGIN_CONFIG_DIR."
    exit 2
fi

if ! install \
    -d \
    -o loxberry \
    -g loxberry \
    -m 0755 \
    "$PLUGIN_DATA_DIR"
then
    echo "<ERROR> Could not create the plugin data directory $PLUGIN_DATA_DIR."
    exit 2
fi

#
# Remove an existing configuration link or file.
#
if [ -e "$CONFIG_LINK" ] || [ -L "$CONFIG_LINK" ]; then
    echo "<INFO> Replacing the existing OwnTracks configuration link."

    if ! rm -f "$CONFIG_LINK"; then
        echo "<ERROR> Could not remove the existing configuration link $CONFIG_LINK."
        exit 2
    fi
fi

#
# Create the configuration link.
#
if ! ln -s "$DEFAULT_FILE" "$CONFIG_LINK"; then
    echo "<ERROR> Could not create the configuration link $CONFIG_LINK."
    exit 2
fi

#
# Remove an existing storage link or file.
#
if [ -e "$STORE_LINK" ] || [ -L "$STORE_LINK" ]; then
    echo "<INFO> Replacing the existing OwnTracks storage link."

    if ! rm -f "$STORE_LINK"; then
        echo "<ERROR> Could not remove the existing storage link $STORE_LINK."
        exit 2
    fi
fi

#
# Create the storage link.
#
if ! ln -s "$STORE_DIR" "$STORE_LINK"; then
    echo "<ERROR> Could not create the storage link $STORE_LINK."
    exit 2
fi

#
# Keep the plugin directories and symbolic links removable by
# the LoxBerry plugin upgrade process.
#
if ! chown \
    loxberry:loxberry \
    "$PLUGIN_CONFIG_DIR" \
    "$PLUGIN_DATA_DIR"
then
    echo "<ERROR> Could not set the owner of the LoxBerry plugin directories."
    exit 2
fi

if ! chown \
    -h \
    loxberry:loxberry \
    "$CONFIG_LINK" \
    "$STORE_LINK"
then
    echo "<ERROR> Could not set the owner of the LoxBerry plugin links."
    exit 2
fi

#
# Reload systemd.
#
echo "<INFO> Reloading systemd unit files."

if ! systemctl daemon-reload; then
    echo "<ERROR> systemd could not reload its unit files."
    exit 2
fi

#
# Enable the service.
#
echo "<INFO> Enabling the OwnTracks Recorder service."

if ! systemctl enable "$SERVICE_NAME" >/dev/null 2>&1; then
    echo "<ERROR> The OwnTracks Recorder service could not be enabled."
    exit 2
fi

#
# Restart the service.
#
echo "<INFO> Starting the OwnTracks Recorder service."

if ! systemctl restart "$SERVICE_NAME"; then
    echo "<WARNING> The OwnTracks Recorder service could not be started."
    echo "<WARNING> The plugin was installed, but the Recorder configuration and service log must be checked."
    exit 1
fi

#
# Verify the service status.
#
if ! systemctl is-active --quiet "$SERVICE_NAME"; then
    echo "<WARNING> The OwnTracks Recorder service is not active after the restart."
    echo "<WARNING> Check $DEFAULT_FILE and run systemctl status $SERVICE_NAME."
    exit 1
fi

echo "<OK> The OwnTracks Recorder was installed and started successfully."

exit 0