import sys

from vm_manager import (
    get_vm_status,
    get_vm_vcpus,
    get_vm_ram,
    get_vm_ip,
    start_vm,
    shutdown_vm,
    reboot_vm,
    get_all_vms_info
)

from connection import connect_to_vm
from launcher import launch_vm


def main():
    if len(sys.argv) == 2 and sys.argv[1].lower() == "list":
        vms = get_all_vms_info()

        if not vms:
            print("No virtual machines found.")
            return

        print("Virtual Machines:")
        print()

        for vm in vms:
            print(f"Name: {vm['name']}")
            print(f"Status: {vm['status']}")
            print(f"vCPU: {vm['vcpus'] if vm['vcpus'] is not None else 'Unknown'}")
            print(f"RAM: {vm['ram'] if vm['ram'] is not None else 'Unknown'}")
            print(f"IP: {vm['ip'] if vm['ip'] is not None else 'Unknown'}")
            print()

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
        result = launch_vm(vm_name)

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