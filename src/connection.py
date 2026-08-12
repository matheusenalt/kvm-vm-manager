import json
import shutil
import subprocess
from pathlib import Path

from vm_manager import get_vm_ip

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "config" / "config.json"
SUPPORTED_CONNECTION_TYPES = {"ssh", "ui", "viewer", "anydesk"}


def load_vm_config(config_path=None):
    path = Path(config_path) if config_path else CONFIG_PATH
    if not path.exists():
        return {}

    try:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except (json.JSONDecodeError, OSError) as error:
        print(f"Could not load configuration: {error}")
        return {}

    return data if isinstance(data, dict) else {}


def save_vm_config(config):
    try:
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        temp_path = CONFIG_PATH.with_suffix(".json.tmp")
        with temp_path.open("w", encoding="utf-8") as file:
            json.dump(config, file, indent=4, ensure_ascii=False)
            file.write("\n")
        temp_path.replace(CONFIG_PATH)
        return True
    except OSError as error:
        print(f"Could not save configuration: {error}")
        return False


def get_vm_config(vm_name):
    vm_config = load_vm_config().get(vm_name)
    return vm_config if isinstance(vm_config, dict) else None


def update_vm_config(vm_name, new_config):
    config = load_vm_config()
    current = config.get(vm_name, {})
    if not isinstance(current, dict):
        current = {}

    updated = {**current, **new_config}
    connection_type = updated.get("connection")

    if connection_type != "anydesk":
        updated.pop("address", None)
    if connection_type != "ssh":
        updated.pop("user", None)
        updated.pop("host", None)

    config[vm_name] = updated
    return save_vm_config(config)


def get_connection_info(vm_name):
    vm_config = get_vm_config(vm_name)
    if vm_config is None:
        return None

    connection_type = str(vm_config.get("connection", "ui")).strip().lower()
    if connection_type == "viewer":
        connection_type = "ui"

    if connection_type not in {"ssh", "ui", "anydesk"}:
        return {
            "type": connection_type,
            "error": f"Unsupported connection type '{connection_type}'.",
        }

    if connection_type == "ssh":
        configured_host = vm_config.get("host")
        return {
            "type": "ssh",
            "user": vm_config.get("user"),
            "host": configured_host or get_vm_ip(vm_name),
            "dynamic_host": configured_host is None,
        }

    if connection_type == "anydesk":
        return {"type": "anydesk", "address": vm_config.get("address")}

    return {"type": "ui"}


def _ssh_command(user, host):
    target = f"{user}@{host}"
    terminals = [
        ("konsole", ["konsole", "-e", "ssh", target]),
        ("gnome-terminal", ["gnome-terminal", "--", "ssh", target]),
        ("xfce4-terminal", ["xfce4-terminal", "-e", f"ssh {target}"]),
        ("kitty", ["kitty", "ssh", target]),
        ("alacritty", ["alacritty", "-e", "ssh", target]),
        ("xterm", ["xterm", "-e", "ssh", target]),
    ]

    for executable, command in terminals:
        if shutil.which(executable):
            return command

    return ["ssh", target]


def connect_to_vm(vm_name):
    connection = get_connection_info(vm_name)
    if connection is None:
        return {
            "success": False,
            "message": f"No connection configuration found for VM '{vm_name}'.",
        }

    if connection.get("error"):
        return {"success": False, "message": connection["error"]}

    connection_type = connection["type"]

    if connection_type == "ui":
        command = ["virt-viewer", "-c", "qemu:///system", vm_name]
        try:
            subprocess.Popen(command)
        except FileNotFoundError:
            return {"success": False, "message": "virt-viewer was not found in PATH."}
        return {"success": True, "message": f"Opening virt-viewer for VM '{vm_name}'."}

    if connection_type == "ssh":
        user = connection.get("user")
        host = connection.get("host")
        if not user:
            return {"success": False, "message": f"SSH user is not configured for VM '{vm_name}'."}
        if not host:
            return {"success": False, "message": "VM IP address is not available."}
        try:
            subprocess.Popen(_ssh_command(user, host))
        except FileNotFoundError:
            return {"success": False, "message": "No SSH client or supported terminal was found."}
        return {"success": True, "message": f"Opening SSH connection to {user}@{host}."}

    address = connection.get("address")
    if not address:
        return {"success": False, "message": "AnyDesk address is not configured."}
    try:
        subprocess.Popen(["anydesk", str(address)])
    except FileNotFoundError:
        return {"success": False, "message": "AnyDesk executable was not found."}
    return {"success": True, "message": f"Opening AnyDesk connection to {address}."}
