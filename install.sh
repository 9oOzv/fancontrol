#!/usr/bin/env bash
set -euo pipefail
shopt -s inherit_errexit
 cd "$(dirname "$0")"

 sudo cp fancontrol.service /etc/systemd/system/
 sudo systemctl daemon-reload
 sudo systemctl enable --now fancontrol.service
