import sys

from vm_manager import (
    RUNNING_STATES,
    STOPPED_STATES,
    get_all_vms_info,
    get_vm_ip,
    get_vm_ram,
    get_vm_status,
    get_vm_vcpus,
    reboot_vm,
    shutdown_vm,
    start_vm
)

from connection import connect_to_vm
from launcher import launch_vm


def print_usage():
    print("Usage:")
    print("  python src/main.py list")
    print("  python src/main.py <vm_name> <command>")
    print("  python src/main.py <vm_name> --widget")
    print()
    print("Commands:")
    print("  list")
    print("  status")
    print("  start")
    print("  shutdown")
    print("  reboot")
    print("  connect")
    print("  launch")
    print("  --widget")


def show_vm_list():
    vms = get_all_vms_info()

    if not vms:
        print("No virtual machines found.")
        return

    print("Virtual Machines:")
    print()

    for vm in vms:
        print(f"Name: {vm['name']}")
        print(f"Status: {vm['status']}")
        print(f"vCPU: {vm['vcpus'] or 'Unknown'}")
        print(f"RAM: {vm['ram'] or 'Unknown'}")
        print(f"IP: {vm['ip'] or 'Unknown'}")
        print()


def open_widget(vm_name):
    if get_vm_status(vm_name) is None:
        print(f"Error: VM '{vm_name}' was not found.")
        return

    # Lazy import keeps CLI-only usage independent from GUI startup.
    from gui import run_widget
    run_widget(vm_name)


def main():
    if len(sys.argv) == 2 and sys.argv[1].lower() == "list":
        show_vm_list()
        return

    if len(sys.argv) == 3 and sys.argv[2].lower() == "--widget":
        open_widget(sys.argv[1])
        return

    if len(sys.argv) < 3:
        print_usage()
        return

    vm_name = sys.argv[1]
    command = sys.argv[2].lower()
    status = get_vm_status(vm_name)

    if status is None:
        print(f"Error: VM '{vm_name}' was not found.")
        return

    normalized_status = status.strip().lower()

    if command == "status":
        vcpus = get_vm_vcpus(vm_name)
        ram = get_vm_ram(vm_name)
        ip = get_vm_ip(vm_name)

        print(f"VM: {vm_name}")
        print(f"Status: {status}")
        print(f"vCPU: {vcpus or 'Unknown'}")
        print(f"RAM: {ram or 'Unknown'}")
        print(f"IP: {ip or 'Unknown'}")

    elif command == "start":
        if normalized_status in RUNNING_STATES:
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
        if normalized_status in STOPPED_STATES:
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
        if normalized_status in STOPPED_STATES:
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

    elif command == "launch":
        result = launch_vm(vm_name)
        print(result["message"])

    else:
        print(f"Error: unknown command '{command}'.")
        print_usage()


if __name__ == "__main__":
    main()
