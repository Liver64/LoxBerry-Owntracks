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

DEFAULT_FILE="/etc/default/ot-recorder"
STORE_DIR="/var/spool/owntracks/recorder/store"

PLUGIN_CONFIG_DIR="REPLACELBPCONFIGDIR/recorder"
PLUGIN_DATA_DIR="REPLACELBPDATADIR/recorder"

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

systemctl daemon-reload

if systemctl cat "$SERVICE_NAME" >/dev/null 2>&1; then
    echo "<OK> The OwnTracks systemd service is available."
else
    echo "<WARNING> No OwnTracks systemd service was installed by the package."
    echo "<INFO> Creating the OwnTracks systemd service."

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
Restart=on-failure
RestartSec=5

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

    if ! systemctl daemon-reload; then
        echo "<ERROR> systemd could not reload its unit files."
        exit 2
    fi

    if ! systemctl cat "$SERVICE_NAME" >/dev/null 2>&1; then
        echo "<ERROR> The OwnTracks systemd service is still unavailable."
        exit 2
    fi

    echo "<OK> The OwnTracks systemd service was created successfully."
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