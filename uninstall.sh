#!/usr/bin/env bash
set -euo pipefail

DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}"
APP_DIR="$DATA_HOME/kvm-vm-manager"
APPLICATIONS_DIR="$DATA_HOME/applications"
DESKTOP_FILE="$APPLICATIONS_DIR/kvm-vm-manager.desktop"
LAUNCHER="$HOME/.local/bin/kvm-vm-manager"

rm -f "$DESKTOP_FILE" "$LAUNCHER"
rm -rf "$APP_DIR"

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$APPLICATIONS_DIR" >/dev/null 2>&1 || true
fi

printf 'KVM VM Manager removed.\n'
