import json
import subprocess
from pathlib import Path

from vm_manager import get_vm_ip


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "config" / "config.json"

SUPPORTED_CONNECTION_TYPES = {
    "ssh",
    "ui",
    "viewer",
    "anydesk"
}


# =========================================================
# CONFIG
# =========================================================

def load_vm_config(config_path=None):
    path = (
        Path(config_path)
        if config_path
        else CONFIG_PATH
    )

    if not path.exists():
        print(
            f"Configuration file not found: {path}"
        )
        return {}

    try:
        with path.open(
            "r",
            encoding="utf-8"
        ) as file:
            data = json.load(file)

    except json.JSONDecodeError as error:
        print(
            f"Invalid JSON configuration: {error}"
        )
        return {}

    except OSError as error:
        print(
            f"Could not read configuration: {error}"
        )
        return {}

    if not isinstance(data, dict):
        return {}

    return data


def save_vm_config(config):
    try:
        CONFIG_PATH.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        temp_path = CONFIG_PATH.with_suffix(
            ".json.tmp"
        )

        with temp_path.open(
            "w",
            encoding="utf-8"
        ) as file:
            json.dump(
                config,
                file,
                indent=4,
                ensure_ascii=False
            )

            file.write("\n")

        temp_path.replace(
            CONFIG_PATH
        )

        return True

    except OSError as error:
        print(
            f"Could not save configuration: {error}"
        )

        return False


def get_vm_config(vm_name):
    config = load_vm_config()

    vm_config = config.get(
        vm_name
    )

    if not isinstance(
        vm_config,
        dict
    ):
        return None

    return vm_config


def update_vm_config(
    vm_name,
    new_config
):
    config = load_vm_config()

    current = config.get(
        vm_name,
        {}
    )

    if not isinstance(
        current,
        dict
    ):
        current = {}

    # Preserva informações como "os"
    updated = {
        **current,
        **new_config
    }

    # Remove propriedades antigas de outro
    # tipo de conexão.
    connection_type = updated.get(
        "connection"
    )

    if connection_type != "anydesk":
        updated.pop(
            "address",
            None
        )

    if connection_type != "ssh":
        updated.pop(
            "user",
            None
        )

        updated.pop(
            "host",
            None
        )

    config[
        vm_name
    ] = updated

    return save_vm_config(
        config
    )


# =========================================================
# CONNECTION INFORMATION
# =========================================================

def get_connection_info(vm_name):
    vm_config = get_vm_config(
        vm_name
    )

    if vm_config is None:
        return None

    connection_type = str(
        vm_config.get(
            "connection",
            "ui"
        )
    ).strip().lower()

    # "viewer" funciona como alias de "ui".
    if connection_type == "viewer":
        connection_type = "ui"

    if connection_type not in {
        "ssh",
        "ui",
        "anydesk"
    }:
        return {
            "type": connection_type,
            "error": (
                "Unsupported connection "
                f"type '{connection_type}'."
            )
        }

    if connection_type == "ssh":
        configured_host = (
            vm_config.get("host")
        )

        host = (
            configured_host
            or get_vm_ip(vm_name)
        )

        return {
            "type": "ssh",
            "user": vm_config.get(
                "user"
            ),
            "host": host,
            "dynamic_host": (
                configured_host is None
            )
        }

    if connection_type == "ui":
        return {
            "type": "ui"
        }

    if connection_type == "anydesk":
        return {
            "type": "anydesk",
            "address": vm_config.get(
                "address"
            )
        }

    return None


# =========================================================
# CONNECT
# =========================================================

def connect_to_vm(vm_name):
    connection = get_connection_info(
        vm_name
    )

    if connection is None:
        return {
            "success": False,
            "message": (
                "No connection configuration "
                f"found for VM '{vm_name}'."
            )
        }

    if connection.get("error"):
        return {
            "success": False,
            "message": connection["error"]
        }

    connection_type = (
        connection["type"]
    )

    # -----------------------------------------------------
    # UI / VIRT-VIEWER
    # -----------------------------------------------------

    if connection_type == "ui":
        try:
            subprocess.Popen([
                "virt-viewer",
                "-c",
                "qemu:///system",
                vm_name
            ])

        except FileNotFoundError:
            return {
                "success": False,
                "message": (
                    "virt-viewer was not found "
                    "in the system PATH."
                )
            }

        return {
            "success": True,
            "message": (
                f"Opening virt-viewer for "
                f"VM '{vm_name}'."
            )
        }

    # -----------------------------------------------------
    # SSH
    # -----------------------------------------------------

    if connection_type == "ssh":
        user = connection.get(
            "user"
        )

        host = connection.get(
            "host"
        )

        if not user:
            return {
                "success": False,
                "message": (
                    f"SSH user is not configured "
                    f"for VM '{vm_name}'."
                )
            }

        if not host:
            return {
                "success": False,
                "message": (
                    "VM IP address "
                    "is not available."
                )
            }

        try:
            subprocess.Popen([
                "ssh",
                f"{user}@{host}"
            ])

        except FileNotFoundError:
            return {
                "success": False,
                "message": (
                    "SSH executable "
                    "was not found."
                )
            }

        return {
            "success": True,
            "message": (
                f"Opening SSH connection "
                f"to {user}@{host}."
            )
        }

    # -----------------------------------------------------
    # ANYDESK
    # -----------------------------------------------------

    if connection_type == "anydesk":
        address = connection.get(
            "address"
        )

        if not address:
            return {
                "success": False,
                "message": (
                    "AnyDesk address "
                    "is not configured."
                )
            }

        try:
            subprocess.Popen([
                "anydesk",
                str(address)
            ])

        except FileNotFoundError:
            return {
                "success": False,
                "message": (
                    "AnyDesk executable "
                    "was not found."
                )
            }

        return {
            "success": True,
            "message": (
                f"Opening AnyDesk "
                f"connection to {address}."
            )
        }

    return {
        "success": False,
        "message": (
            f"Unsupported connection "
            f"type '{connection_type}'."
        )
    }