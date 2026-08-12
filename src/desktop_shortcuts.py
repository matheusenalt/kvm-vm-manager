import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

from connection import get_vm_config
from os_catalog import get_logo_key

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _desktop_dir():
    if shutil.which("xdg-user-dir"):
        result = subprocess.run(
            ["xdg-user-dir", "DESKTOP"],
            capture_output=True,
            text=True,
            check=False,
        )
        value = result.stdout.strip()
        if value:
            return Path(value).expanduser()
    return Path.home() / "Desktop"


def _desktop_exec_quote(value):
    return '"' + str(value).replace("\\", "\\\\").replace('"', '\\"') + '"'


def _app_command(vm_name):
    installed = shutil.which("kvm-vm-manager")
    if installed:
        return f'{_desktop_exec_quote(installed)} {_desktop_exec_quote(vm_name)} --widget'

    main_path = PROJECT_ROOT / "src" / "main.py"
    return (
        f'{_desktop_exec_quote(sys.executable)} '
        f'{_desktop_exec_quote(main_path)} '
        f'{_desktop_exec_quote(vm_name)} --widget'
    )


def _shortcut_icon(vm_name):
    config = get_vm_config(vm_name) or {}
    logo_key = get_logo_key(config.get("os", "linux"))
    candidates = [
        PROJECT_ROOT / "assets" / f"{logo_key}.png",
        PROJECT_ROOT / "assets" / "app-icon.png",
        PROJECT_ROOT / "assets" / "app-icon.svg",
    ]
    for path in candidates:
        if path.exists():
            return str(path)
    return "computer"


def create_widget_shortcut(vm_name):
    desktop = _desktop_dir()
    desktop.mkdir(parents=True, exist_ok=True)

    safe_name = "".join(
        char if char.isalnum() or char in "-_." else "-"
        for char in vm_name
    ).strip("-") or "vm"

    shortcut = desktop / f"kvm-vm-manager-{safe_name}.desktop"
    icon = _shortcut_icon(vm_name)
    content = "\n".join([
        "[Desktop Entry]",
        "Type=Application",
        f"Name={vm_name}",
        f"Comment=Open {vm_name} KVM mini widget",
        f"Exec={_app_command(vm_name)}",
        f"Icon={icon}",
        "Terminal=false",
        "Categories=System;Utility;",
        "StartupNotify=true",
        "",
    ])

    shortcut.write_text(content, encoding="utf-8")
    shortcut.chmod(shortcut.stat().st_mode | stat.S_IXUSR)

    return {
        "success": True,
        "message": f"Shortcut created: {shortcut}",
        "path": str(shortcut),
    }


def remove_widget_shortcut(vm_name):
    desktop = _desktop_dir()
    safe_name = "".join(
        char if char.isalnum() or char in "-_." else "-"
        for char in vm_name
    ).strip("-") or "vm"
    shortcut = desktop / f"kvm-vm-manager-{safe_name}.desktop"

    if not shortcut.exists():
        return {
            "success": False,
            "message": "Desktop shortcut does not exist.",
        }

    shortcut.unlink()
    return {
        "success": True,
        "message": f"Shortcut removed: {shortcut}",
    }
