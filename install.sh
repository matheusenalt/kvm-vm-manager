#!/usr/bin/env bash
set -euo pipefail

SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}"
BIN_HOME="${HOME}/.local/bin"
APP_DIR="$DATA_HOME/kvm-vm-manager"
APPLICATIONS_DIR="$DATA_HOME/applications"
DESKTOP_FILE="$APPLICATIONS_DIR/kvm-vm-manager.desktop"
LAUNCHER="$BIN_HOME/kvm-vm-manager"

for command in python virsh virt-install virt-viewer; do
    if ! command -v "$command" >/dev/null 2>&1; then
        printf 'Missing system command: %s\n' "$command"
        exit 1
    fi
done

if ! python -c 'import tkinter' >/dev/null 2>&1; then
    printf 'Python Tk support is missing. On Manjaro install the tk package.\n'
    exit 1
fi

if ! virsh -c qemu:///system list --all >/dev/null 2>&1; then
    printf 'Could not connect to libvirt at qemu:///system with the current user.\n'
    exit 1
fi

mkdir -p "$APP_DIR" "$BIN_HOME" "$APPLICATIONS_DIR"
CONFIG_BACKUP=""
if [ -f "$APP_DIR/config/config.json" ]; then
    CONFIG_BACKUP="$(mktemp)"
    cp "$APP_DIR/config/config.json" "$CONFIG_BACKUP"
fi
find "$APP_DIR" -mindepth 1 -maxdepth 1 -exec rm -rf {} +

tar \
    --exclude='.git' \
    --exclude='.venv' \
    --exclude='__pycache__' \
    --exclude='config/config.json' \
    -C "$SOURCE_DIR" -cf - . | tar -C "$APP_DIR" -xf -

python -m venv "$APP_DIR/.venv"
"$APP_DIR/.venv/bin/python" -m pip install --upgrade pip
"$APP_DIR/.venv/bin/python" -m pip install -r "$APP_DIR/requirements.txt"

if [ -n "$CONFIG_BACKUP" ] && [ -f "$CONFIG_BACKUP" ]; then
    cp "$CONFIG_BACKUP" "$APP_DIR/config/config.json"
    rm -f "$CONFIG_BACKUP"
elif [ -f "$SOURCE_DIR/config/config.json" ]; then
    cp "$SOURCE_DIR/config/config.json" "$APP_DIR/config/config.json"
elif [ ! -f "$APP_DIR/config/config.json" ]; then
    cp "$APP_DIR/config/example.json" "$APP_DIR/config/config.json"
fi

cat > "$LAUNCHER" <<EOF
#!/usr/bin/env bash
set -e
APP_DIR="$APP_DIR"
exec "\$APP_DIR/.venv/bin/python" "\$APP_DIR/src/main.py" "\$@"
EOF
chmod +x "$LAUNCHER"

ICON_VALUE="computer"
if [ -f "$APP_DIR/assets/app-icon.png" ]; then
    ICON_VALUE="$APP_DIR/assets/app-icon.png"
elif [ -f "$APP_DIR/assets/app-icon.svg" ]; then
    ICON_VALUE="$APP_DIR/assets/app-icon.svg"
fi

cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Type=Application
Name=KVM VM Manager
Comment=Manage local KVM/libvirt virtual machines
Exec=$LAUNCHER
Icon=$ICON_VALUE
Terminal=false
Categories=System;Utility;
StartupNotify=true
EOF
chmod +x "$DESKTOP_FILE"

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$APPLICATIONS_DIR" >/dev/null 2>&1 || true
fi

printf 'KVM VM Manager installed.\n'
printf 'Launcher: %s\n' "$LAUNCHER"
printf 'Desktop entry: %s\n' "$DESKTOP_FILE"
