import time

from vm_manager import (
    RUNNING_STATES,
    get_vm_ip,
    get_vm_status,
    start_vm
)

from connection import (
    connect_to_vm,
    get_connection_info
)


def wait_for_guest_network(
    vm_name,
    max_attempts=60,
    wait_seconds=2
):
    for attempt in range(
        max_attempts
    ):
        ip = get_vm_ip(
            vm_name
        )

        if ip:
            print(
                f"VM network available: {ip}"
            )

            return ip

        print(
            "Waiting for network... "
            f"({attempt + 1}/"
            f"{max_attempts})"
        )

        time.sleep(
            wait_seconds
        )

    return None


def launch_vm(vm_name):
    status = get_vm_status(
        vm_name
    )

    if status is None:
        return {
            "success": False,
            "message": (
                f"VM '{vm_name}' "
                "was not found."
            )
        }

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
            "message": connection[
                "error"
            ]
        }

    connection_type = (
        connection.get("type")
    )

    normalized_status = (
        status.strip().lower()
    )

    vm_was_started = False

    # =====================================================
    # START VM
    # =====================================================

    if normalized_status not in (
        RUNNING_STATES
    ):
        print(
            f"Starting VM '{vm_name}'..."
        )

        result = start_vm(
            vm_name
        )

        if result.returncode != 0:
            error = (
                result.stderr.strip()
                if result.stderr
                else ""
            )

            return {
                "success": False,
                "message": (
                    f"Could not start "
                    f"VM '{vm_name}'. "
                    f"{error}"
                ).strip()
            }

        vm_was_started = True

        print(
            "VM started successfully."
        )

    # =====================================================
    # SSH
    # =====================================================

    if (
        vm_was_started
        and connection_type == "ssh"
        and connection.get(
            "dynamic_host",
            True
        )
    ):
        print(
            "Waiting for guest network..."
        )

        ip = wait_for_guest_network(
            vm_name
        )

        if not ip:
            return {
                "success": False,
                "message": (
                    "VM network was not "
                    "available in time."
                )
            }

    # =====================================================
    # ANYDESK
    # =====================================================

    if (
        vm_was_started
        and connection_type == "anydesk"
    ):
        print(
            "Waiting for guest network..."
        )

        ip = wait_for_guest_network(
            vm_name
        )

        if not ip:
            return {
                "success": False,
                "message": (
                    "VM network was not "
                    "available in time."
                )
            }

        print(
            "Waiting for AnyDesk..."
        )

        time.sleep(
            15
        )

    # =====================================================
    # UI / VIRT-VIEWER
    # =====================================================

    # virt-viewer não precisa esperar IP.
    # Ele conecta diretamente ao libvirt.
    if connection_type == "ui":
        print(
            "Opening virt-viewer..."
        )

        return connect_to_vm(
            vm_name
        )

    # =====================================================
    # OTHER CONNECTIONS
    # =====================================================

    print(
        f"Opening {connection_type} "
        "connection..."
    )

    return connect_to_vm(
        vm_name
    )