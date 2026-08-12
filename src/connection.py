import json
import subprocess
from pathlib import Path

from vm_manager import get_vm_ip


def load_vm_config():
    config_path = Path("config/config.json")

    if not config_path.exists():
        print(
            "Configuration file not found.\n"
            "Create 'config/config.json' based on "
            "'config/example.json'."
        )
        return {}

    try:
        with open(config_path, "r", encoding="utf-8") as file:
            return json.load(file)

    except json.JSONDecodeError:
        print("Error: invalid JSON configuration.")
        return {}


def get_connection_info(vm_name):
    config = load_vm_config()

    vm_config = config.get(vm_name)

    if vm_config is None:
        return None

    connection_type = vm_config.get("connection")

    if connection_type == "ssh":
        return {
            "type": "ssh",
            "user": vm_config.get("user"),
            "host": get_vm_ip(vm_name)
        }

    if connection_type == "anydesk":
        return {
            "type": "anydesk",
            "address": vm_config.get("address")
        }

    return None


def connect_to_vm(vm_name):
    connection = get_connection_info(vm_name)

    if connection is None:
        return {
            "success": False,
            "message": (
                f"No connection configuration found "
                f"for VM '{vm_name}'."
            )
        }

    if connection["type"] == "ssh":
        user = connection.get("user")
        host = connection.get("host")

        if not user:
            return {
                "success": False,
                "message": "SSH user is not configured."
            }

        if not host:
            return {
                "success": False,
                "message": "VM IP address is not available."
            }

        subprocess.run(
            ["ssh", f"{user}@{host}"]
        )

        return {
            "success": True,
            "message": (
                f"SSH connection closed for "
                f"{user}@{host}."
            )
        }

    if connection["type"] == "anydesk":
        address = connection.get("address")

        if not address:
            return {
                "success": False,
                "message": "AnyDesk address is not configured."
            }

        try:
            subprocess.Popen(
                ["anydesk", address]
            )

        except FileNotFoundError:
            return {
                "success": False,
                "message": (
                    "AnyDesk executable was not found "
                    "in the system PATH."
                )
            }

        return {
            "success": True,
            "message": (
                f"Opening AnyDesk connection to "
                f"{address}."
            )
        }

    return {
        "success": False,
        "message": "Unsupported connection type."
    }