import sys

from connection import connect_to_vm
from desktop_shortcuts import create_widget_shortcut
from launcher import launch_vm
from vm_manager import (
    RUNNING_STATES,
    STOPPED_STATES,
    get_all_vms_info,
    get_available_os_variants,
    get_vm_ip,
    get_vm_ram,
    get_vm_status,
    get_vm_vcpus,
    reboot_vm,
    shutdown_vm,
    start_vm,
)


def print_usage():
    print("Usage:")
    print("  kvm-vm-manager")
    print("  kvm-vm-manager list")
    print("  kvm-vm-manager list-os")
    print("  kvm-vm-manager <vm_name> <command>")
    print("  kvm-vm-manager <vm_name> --widget")
    print()
    print("Commands:")
    print("  status")
    print("  start")
    print("  shutdown")
    print("  reboot")
    print("  connect")
    print("  launch")
    print("  shortcut")
    print("  --widget")


def open_gui():
    from ui.main_window import VMManagerApp
    app = VMManagerApp()
    app.mainloop()


def show_vm_list():
    vms = get_all_vms_info()
    if not vms:
        print("No virtual machines found.")
        return

    for vm in vms:
        print(f"Name: {vm['name']}")
        print(f"Status: {vm['status']}")
        print(f"vCPU: {vm['vcpus'] or 'Unknown'}")
        print(f"RAM: {vm['ram'] or 'Unknown'}")
        print(f"IP: {vm['ip'] or 'Unknown'}")
        print()


def show_os_list():
    variants = get_available_os_variants()
    if not variants:
        print("No libosinfo variants were found.")
        return
    for variant in variants:
        print(variant)


def open_widget(vm_name):
    if get_vm_status(vm_name) is None:
        print(f"Error: VM '{vm_name}' was not found.")
        return
    from widget import run_widget
    run_widget(vm_name)


def run_vm_command(vm_name, command):
    status = get_vm_status(vm_name)
    if status is None:
        print(f"Error: VM '{vm_name}' was not found.")
        return

    normalized_status = status.strip().lower()

    if command == "status":
        print(f"VM: {vm_name}")
        print(f"Status: {status}")
        print(f"vCPU: {get_vm_vcpus(vm_name) or 'Unknown'}")
        print(f"RAM: {get_vm_ram(vm_name) or 'Unknown'}")
        print(f"IP: {get_vm_ip(vm_name) or 'Unknown'}")
        return

    if command == "start":
        if normalized_status in RUNNING_STATES:
            print(f"VM '{vm_name}' is already running.")
            return
        result = start_vm(vm_name)
        print(result.stderr.strip() if result.returncode != 0 else f"VM '{vm_name}' started successfully.")
        return

    if command == "shutdown":
        if normalized_status in STOPPED_STATES:
            print(f"VM '{vm_name}' is already powered off.")
            return
        result = shutdown_vm(vm_name)
        print(result.stderr.strip() if result.returncode != 0 else f"Shutdown signal sent to VM '{vm_name}'.")
        return

    if command == "reboot":
        if normalized_status in STOPPED_STATES:
            print(f"Error: VM '{vm_name}' is powered off.")
            return
        result = reboot_vm(vm_name)
        print(result.stderr.strip() if result.returncode != 0 else f"Reboot signal sent to VM '{vm_name}'.")
        return

    if command == "connect":
        print(connect_to_vm(vm_name)["message"])
        return

    if command == "launch":
        print(launch_vm(vm_name)["message"])
        return

    if command == "shortcut":
        print(create_widget_shortcut(vm_name)["message"])
        return

    print(f"Error: unknown command '{command}'.")
    print_usage()


def main():
    args = sys.argv[1:]

    if not args or args == ["gui"]:
        open_gui()
        return

    if len(args) == 1 and args[0].lower() == "list":
        show_vm_list()
        return

    if len(args) == 1 and args[0].lower() == "list-os":
        show_os_list()
        return

    if len(args) == 2 and args[1].lower() == "--widget":
        open_widget(args[0])
        return

    if len(args) == 2:
        run_vm_command(args[0], args[1].lower())
        return

    print_usage()


if __name__ == "__main__":
    main()
