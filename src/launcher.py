import time

from vm_manager import (
    get_vm_status,
    get_vm_ip,
    start_vm
)

from connection import (
    connect_to_vm,
    get_connection_info
)


def launch_vm(vm_name):
    status = get_vm_status(vm_name)

    if status is None:
        return {
            "success": False,
            "message": f"VM '{vm_name}' was not found."
        }

    vm_was_started = False

    if status not in ("running", "executando"):
        print(f"Starting VM '{vm_name}'...")

        result = start_vm(vm_name)

        if result.returncode != 0:
            return {
                "success": False,
                "message": f"Could not start VM '{vm_name}'."
            }

        print("VM started successfully.")
        vm_was_started = True

    connection = get_connection_info(vm_name)

    if connection is None:
        return {
            "success": False,
            "message": (
                f"No connection configuration found "
                f"for VM '{vm_name}'."
            )
        }

    connection_type = connection.get("type")

    if vm_was_started:
        print("Waiting for guest network...")

        max_attempts = 60
        wait_seconds = 2
        ip = None

        for attempt in range(max_attempts):
            ip = get_vm_ip(vm_name)

            if ip:
                print(f"VM network available: {ip}")
                break

            print(
                f"Waiting for network... "
                f"({attempt + 1}/{max_attempts})"
            )

            time.sleep(wait_seconds)

        if not ip:
            return {
                "success": False,
                "message": "VM network was not available in time."
            }

        if connection_type == "anydesk":
            print("Waiting for remote desktop service...")
            time.sleep(15)

    print("Opening connection...")

    return connect_to_vm(vm_name)