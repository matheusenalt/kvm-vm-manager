import subprocess


def run_virsh_command(command_args):
    return subprocess.run(
        ["virsh", "--connect", "qemu:///system"] + command_args,
        capture_output=True,
        text=True
    )


def get_vm_status(vm_name):
    result = run_virsh_command(["domstate", vm_name])

    if result.returncode != 0:
        return None

    return result.stdout.strip()


def get_vm_info(vm_name):
    result = run_virsh_command(["dominfo", vm_name])

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
    result = run_virsh_command(["dommemstat", vm_name])

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
    result = run_virsh_command(["domifaddr", vm_name])

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
    return run_virsh_command(["start", vm_name])


def shutdown_vm(vm_name):
    return run_virsh_command(["shutdown", vm_name])


def reboot_vm(vm_name):
    return run_virsh_command(["reboot", vm_name])

def list_vms():
    result = run_virsh_command(
        ["list", "--all", "--name"]
    )

    if result.returncode != 0:
        return []

    vms = []

    for line in result.stdout.splitlines():
        vm_name = line.strip()

        if vm_name:
            vms.append(vm_name)

    return vms    