import sys
import time

from vm_manager import (
    get_vm_status,
    get_vm_vcpus,
    get_vm_ram,
    get_vm_ip,
    start_vm,
    shutdown_vm,
    reboot_vm,
    list_vms
)

from connection import (
    connect_to_vm,
    get_connection_info
)


def main():
    if len(sys.argv) == 2 and sys.argv[1].lower() == "list":
        vms = list_vms()

        if not vms:
            print("No virtual machines found.")
            return

        print("Virtual Machines:")
        print()

        for vm_name in vms:
            status = get_vm_status(vm_name)
            print(f"{vm_name}: {status}")

        return

    if len(sys.argv) < 3:
        print("Usage:")
        print("  python src/main.py list")
        print("  python src/main.py <vm_name> <command>")
        print()
        print("Commands:")
        print("  list")
        print("  status")
        print("  start")
        print("  shutdown")
        print("  reboot")
        print("  connect")
        print("  launch")
        return

    vm_name = sys.argv[1]
    command = sys.argv[2].lower()

    status = get_vm_status(vm_name)

    if status is None:
        print(f"Error: VM '{vm_name}' was not found.")
        return

    if command == "status":
        vcpus = get_vm_vcpus(vm_name)
        ram = get_vm_ram(vm_name)
        ip = get_vm_ip(vm_name)

        print(f"VM: {vm_name}")
        print(f"Status: {status}")
        print(f"vCPU: {vcpus if vcpus is not None else 'Unknown'}")
        print(f"RAM: {ram if ram is not None else 'Unknown'}")
        print(f"IP: {ip if ip is not None else 'Unknown'}")

    elif command == "start":
        if status in ("running", "executando"):
            print(f"VM '{vm_name}' is already running.")
            return

        result = start_vm(vm_name)

        if result.returncode != 0:
            print(f"Error: could not start VM '{vm_name}'.")

            if result.stderr:
                print(result.stderr.strip())

            return

        print(f"VM '{vm_name}' started successfully.")

    elif command == "shutdown":
        if status in ("shut off", "desligado"):
            print(f"VM '{vm_name}' is already powered off.")
            return

        result = shutdown_vm(vm_name)

        if result.returncode != 0:
            print(f"Error: could not shutdown VM '{vm_name}'.")

            if result.stderr:
                print(result.stderr.strip())

            return

        print(f"Shutdown signal sent to VM '{vm_name}'.")

    elif command == "reboot":
        if status in ("shut off", "desligado"):
            print(f"Error: VM '{vm_name}' is powered off.")
            return

        result = reboot_vm(vm_name)

        if result.returncode != 0:
            print(f"Error: could not reboot VM '{vm_name}'.")

            if result.stderr:
                print(result.stderr.strip())

            return

        print(f"Reboot signal sent to VM '{vm_name}'.")

    elif command == "connect":
        result = connect_to_vm(vm_name)

        print(result["message"])

        if not result["success"]:
            return

    elif command == "launch":
        vm_was_started = False

        if status not in ("running", "executando"):
            print(f"Starting VM '{vm_name}'...")

            result = start_vm(vm_name)

            if result.returncode != 0:
                print(f"Error: could not start VM '{vm_name}'.")

                if result.stderr:
                    print(result.stderr.strip())

                return

            print("VM started successfully.")
            vm_was_started = True

        connection = get_connection_info(vm_name)

        if connection is None:
            print(
                f"No connection configuration found "
                f"for VM '{vm_name}'."
            )
            return

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
                print("Error: VM network was not available in time.")
                return

            if connection_type == "anydesk":
                print("Waiting for remote desktop service...")
                time.sleep(15)

        print("Opening connection...")

        result = connect_to_vm(vm_name)

        print(result["message"])

        if not result["success"]:
            return

    else:
        print(f"Error: unknown command '{command}'.")
        print()
        print("Available commands:")
        print("  status")
        print("  start")
        print("  shutdown")
        print("  reboot")
        print("  connect")
        print("  launch")


if __name__ == "__main__":
    main()