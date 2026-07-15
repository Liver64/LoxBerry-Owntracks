#!/bin/sh
#
# LoxBerry OwnTracks plugin
# Root pre-installation script
#
# This script runs before LoxBerry refreshes the APT database and
# installs the packages listed in dpkg/apt.
#

set -u

OS_RELEASE="/etc/os-release"

KEY_URL="https://raw.githubusercontent.com/owntracks/recorder/master/etc/repo-v2.owntracks.org.gpg.key"
KEY_FILE="/etc/apt/trusted.gpg.d/owntracks.asc"

SOURCE_FILE="/etc/apt/sources.list.d/owntracks.sources"

KEY_TMP=""
SOURCE_TMP=""

cleanup()
{
    [ -z "$KEY_TMP" ] || rm -f "$KEY_TMP"
    [ -z "$SOURCE_TMP" ] || rm -f "$SOURCE_TMP"
}

trap cleanup EXIT HUP INT TERM

echo "<INFO> Preparing the OwnTracks package repository."

if [ ! -r "$OS_RELEASE" ]; then
    echo "<ERROR> Cannot read $OS_RELEASE. The operating system could not be identified."
    exit 2
fi

. "$OS_RELEASE"

case "${VERSION_ID:-}" in
    12)
        OWNTRACKS_SUITE="bookworm"
        ;;

    13)
        OWNTRACKS_SUITE="trixie"
        ;;

    *)
        echo "<ERROR> Debian ${VERSION_ID:-unknown} is not supported by this OwnTracks plugin."
        echo "<ERROR> Supported versions are Debian 12 Bookworm and Debian 13 Trixie."
        exit 2
        ;;
esac

if ! command -v curl >/dev/null 2>&1; then
    echo "<ERROR> curl is not installed."
    echo "<ERROR> The OwnTracks repository signing key cannot be downloaded."
    exit 2
fi

if ! command -v install >/dev/null 2>&1; then
    echo "<ERROR> The install command is not available."
    exit 2
fi

KEY_TMP="$(mktemp)"

if [ -z "$KEY_TMP" ] || [ ! -f "$KEY_TMP" ]; then
    echo "<ERROR> Could not create a temporary file for the OwnTracks repository signing key."
    exit 2
fi

SOURCE_TMP="$(mktemp)"

if [ -z "$SOURCE_TMP" ] || [ ! -f "$SOURCE_TMP" ]; then
    echo "<ERROR> Could not create a temporary file for the OwnTracks repository definition."
    exit 2
fi

echo "<INFO> Downloading the current OwnTracks repository signing key."

if ! curl -fsSL "$KEY_URL" -o "$KEY_TMP"; then
    echo "<ERROR> Could not download the OwnTracks repository signing key."
    echo "<ERROR> Check the Internet connection and try again."
    exit 2
fi

if [ ! -s "$KEY_TMP" ]; then
    echo "<ERROR> The downloaded OwnTracks repository signing key is empty."
    exit 2
fi

echo "<INFO> Removing obsolete OwnTracks repository definitions."

#
# Remove OwnTracks entries from the main sources.list.
#
if [ -f /etc/apt/sources.list ] &&
   grep -q 'repo\.owntracks\.org' /etc/apt/sources.list; then

    if ! sed -i '\|repo\.owntracks\.org|d' /etc/apt/sources.list; then
        echo "<ERROR> Could not remove the obsolete OwnTracks entry from /etc/apt/sources.list."
        exit 2
    fi
fi

#
# Remove all old OwnTracks .list and .sources files.
# This also removes old Bullseye repository definitions.
#
for OLD_SOURCE in \
    /etc/apt/sources.list.d/*.list \
    /etc/apt/sources.list.d/*.sources
do
    [ -f "$OLD_SOURCE" ] || continue

    if grep -q 'repo\.owntracks\.org' "$OLD_SOURCE"; then
        echo "<INFO> Removing obsolete repository file $OLD_SOURCE."

        if ! rm -f "$OLD_SOURCE"; then
            echo "<ERROR> Could not remove obsolete OwnTracks repository file $OLD_SOURCE."
            exit 2
        fi
    fi
done

#
# Remove signing-key files from older plugin versions.
#
rm -f \
    /etc/apt/trusted.gpg.d/owntracks.gpg \
    /etc/apt/trusted.gpg.d/repo.owntracks.org.gpg \
    /etc/apt/trusted.gpg.d/repo.owntracks.org.asc

echo "<INFO> Installing the current OwnTracks repository signing key."

if ! install \
    -o root \
    -g root \
    -m 0644 \
    "$KEY_TMP" \
    "$KEY_FILE"
then
    echo "<ERROR> Could not install the OwnTracks repository signing key."
    exit 2
fi

echo "<INFO> Creating the OwnTracks repository definition for Debian ${VERSION_ID} ${OWNTRACKS_SUITE}."

cat > "$SOURCE_TMP" <<EOF
Types: deb
URIs: http://repo.owntracks.org/debian/
Suites: ${OWNTRACKS_SUITE}
Components: main
Signed-By: ${KEY_FILE}
EOF

if [ ! -s "$SOURCE_TMP" ]; then
    echo "<ERROR> Could not create the OwnTracks repository definition."
    exit 2
fi

if ! install \
    -o root \
    -g root \
    -m 0644 \
    "$SOURCE_TMP" \
    "$SOURCE_FILE"
then
    echo "<ERROR> Could not install the OwnTracks repository definition."
    exit 2
fi

echo "<OK> The OwnTracks repository for Debian ${VERSION_ID} ${OWNTRACKS_SUITE} is ready."

exit 0