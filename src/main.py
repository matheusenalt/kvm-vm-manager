import sys
import subprocess


def run_virsh_command(command_args):
    result = subprocess.run(
        ["virsh", "--connect", "qemu:///system"] + command_args,
        capture_output=True,
        text=True
    )

    return result


def get_vm_status(vm_name):
    result = run_virsh_command(
        ["domstate", vm_name]
    )

    if result.returncode != 0:
        return None

    return result.stdout.strip()


def get_vm_info(vm_name):
    result = run_virsh_command(
        ["dominfo", vm_name]
    )

    if result.returncode != 0:
        return None

    info = {}

    for line in result.stdout.splitlines():
        if ":" not in line:
            continue

        key, value = line.split(":", 1)
        info[key.strip()] = value.strip()

    return info


def get_vm_vcpus(vm_name):
    info = get_vm_info(vm_name)

    if info is None:
        return None

    return info.get("CPU(s)")


def get_vm_ram(vm_name):
    result = run_virsh_command(
        ["dommemstat", vm_name]
    )

    if result.returncode != 0:
        return None

    for line in result.stdout.splitlines():
        parts = line.split()

        if len(parts) != 2:
            continue

        if parts[0] == "actual":
            try:
                memory_kib = int(parts[1])
            except ValueError:
                return None

            memory_gb = memory_kib / 1024 / 1024

            return f"{memory_gb:.2f} GB"

    return None


def get_vm_ip(vm_name):
    result = run_virsh_command(
        ["domifaddr", vm_name]
    )

    if result.returncode != 0:
        return None

    for line in result.stdout.splitlines():
        parts = line.split()

        if len(parts) < 4:
            continue

        address = parts[-1]

        if "/" in address and "." in address:
            return address.split("/")[0]

    return None


def start_vm(vm_name):
    return run_virsh_command(
        ["start", vm_name]
    )


def shutdown_vm(vm_name):
    return run_virsh_command(
        ["shutdown", vm_name]
    )


def reboot_vm(vm_name):
    return run_virsh_command(
        ["reboot", vm_name]
    )


def main():
    if len(sys.argv) < 3:
        print("Usage: python src/main.py <vm_name> <command>")
        print()
        print("Commands:")
        print("  status")
        print("  start")
        print("  shutdown")
        print("  reboot")
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

    else:
        print(f"Error: unknown command '{command}'.")
        print()
        print("Available commands:")
        print("  status")
        print("  start")
        print("  shutdown")
        print("  reboot")


if __name__ == "__main__":
    main()