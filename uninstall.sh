#!/usr/bin/env bash
set -euo pipefail
shopt -s inherit_errexit
 cd "$(dirname "$0")"

 sudo systemctl disable --now fancontrol.service
 sudo rm /etc/systemd/system/fancopntrol.service || true
 sudo systemctl daemon-reload
