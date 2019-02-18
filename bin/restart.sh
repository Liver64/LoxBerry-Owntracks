#!/bin/sh

# Restart Service
sudo ot-recorder --initialize
sudo systemctl reload-or-restart ot-recorder &

exit 0
