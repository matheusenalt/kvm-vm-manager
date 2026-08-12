import re
import shutil
import subprocess
from pathlib import Path


RUNNING_STATES = {"running", "executando"}
STOPPED_STATES = {"shut off", "desligado", "desligada"}

OS_VARIANT_CANDIDATES = {
    "ubuntu": ["ubuntu24.04", "ubuntu22.04", "ubuntu20.04"],
    "mint": ["linuxmint22", "linuxmint21.3", "ubuntu22.04"],
    "debian": ["debian12", "debian11"],
    "windows": ["win11", "win10"],
}


def run_virsh_command(command_args):
    command = ["virsh", "--connect", "qemu:///system"] + command_args

    try:
        return subprocess.run(
            command,
            capture_output=True,
            text=True
        )
    except FileNotFoundError:
        return subprocess.CompletedProcess(
            command,
            127,
            stdout="",
            stderr="virsh executable was not found in PATH."
        )


def get_vm_status(vm_name):
    result = run_virsh_command(["domstate", vm_name])

    if result.returncode != 0:
        return None

    return result.stdout.strip()


def is_vm_running(vm_name_or_status):
    if vm_name_or_status is None:
        return False

    value = str(vm_name_or_status).strip().lower()

    if value in RUNNING_STATES:
        return True

    status = get_vm_status(value)
    return bool(status and status.strip().lower() in RUNNING_STATES)


def is_vm_stopped(vm_name_or_status):
    if vm_name_or_status is None:
        return False

    value = str(vm_name_or_status).strip().lower()

    if value in STOPPED_STATES:
        return True

    status = get_vm_status(value)
    return bool(status and status.strip().lower() in STOPPED_STATES)


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
    result = run_virsh_command(["list", "--all", "--name"])

    if result.returncode != 0:
        return []

    return [
        line.strip()
        for line in result.stdout.splitlines()
        if line.strip()
    ]


def get_vm_snapshot(vm_name):
    status = get_vm_status(vm_name)

    if status is None:
        return None

    vcpus = get_vm_vcpus(vm_name)
    ram = get_vm_ram(vm_name)
    ip = None

    if status.strip().lower() in RUNNING_STATES:
        ip = get_vm_ip(vm_name)

    return {
        "name": vm_name,
        "status": status,
        "vcpus": vcpus,
        "ram": ram,
        "ip": ip
    }


def get_all_vms_info():
    all_vms = []

    for vm_name in list_vms():
        vm_data = get_vm_snapshot(vm_name)

        if vm_data is not None:
            all_vms.append(vm_data)

    return all_vms


def _available_os_variants():
    if shutil.which("osinfo-query") is None:
        return set()

    try:
        result = subprocess.run(
            ["osinfo-query", "os", "--fields", "short-id"],
            capture_output=True,
            text=True,
            check=False
        )
    except OSError:
        return set()

    if result.returncode != 0:
        return set()

    variants = set()
    for line in result.stdout.splitlines():
        value = line.strip()
        if not value or value.startswith("Short ID") or set(value) == {"-"}:
            continue
        variants.add(value.split()[0])

    return variants


def _select_os_variant(os_name):
    os_name = str(os_name).strip().lower()
    candidates = OS_VARIANT_CANDIDATES.get(os_name, [])
    available = _available_os_variants()

    if available:
        for candidate in candidates:
            if candidate in available:
                return candidate

    # 'generic' is broadly supported and keeps creation portable when the
    # host's osinfo database differs from the developer's machine.
    return "generic"


def create_vm(name, os_name, vcpus, ram_gb, disk_gb, iso_path):
    """Create and start a VM through virt-install.

    This function is intentionally synchronous. The GUI calls it from a
    worker thread so Tk's main loop never blocks.
    """
    name = str(name or "").strip()
    os_name = str(os_name or "").strip().lower()
    iso = Path(str(iso_path or "")).expanduser()

    if not name:
        return {
            "success": False,
            "message": "VM name cannot be empty."
        }

    if not re.fullmatch(r"[A-Za-z0-9._-]+", name):
        return {
            "success": False,
            "message": (
                "VM name may contain only letters, numbers, '.', '_' and '-'."
            )
        }

    if get_vm_status(name) is not None:
        return {
            "success": False,
            "message": f"A VM named '{name}' already exists."
        }

    if os_name not in {"ubuntu", "mint", "debian", "windows"}:
        return {
            "success": False,
            "message": f"Unsupported operating system '{os_name}'."
        }

    try:
        vcpus = int(vcpus)
        ram_gb = int(ram_gb)
        disk_gb = int(disk_gb)
    except (TypeError, ValueError):
        return {
            "success": False,
            "message": "vCPU, RAM and disk size must be whole numbers."
        }

    if not 1 <= vcpus <= 64:
        return {"success": False, "message": "vCPU must be between 1 and 64."}

    if not 1 <= ram_gb <= 512:
        return {"success": False, "message": "RAM must be between 1 and 512 GB."}

    if not 1 <= disk_gb <= 4096:
        return {"success": False, "message": "Disk size must be between 1 and 4096 GB."}

    if not iso.is_file():
        return {
            "success": False,
            "message": f"ISO file was not found: {iso}"
        }

    if shutil.which("virt-install") is None:
        return {
            "success": False,
            "message": (
                "virt-install was not found in PATH. Install the virt-install "
                "package before creating VMs."
            )
        }

    os_variant = _select_os_variant(os_name)
    memory_mb = ram_gb * 1024

    if os_name == "windows":
        disk_bus = "sata"
        network_model = "e1000e"
    else:
        disk_bus = "virtio"
        network_model = "virtio"

    command = [
        "virt-install",
        "--connect", "qemu:///system",
        "--name", name,
        "--vcpus", str(vcpus),
        "--memory", str(memory_mb),
        "--disk", f"size={disk_gb},format=qcow2,bus={disk_bus}",
        "--cdrom", str(iso.resolve()),
        "--network", f"network=default,model={network_model}",
        "--graphics", "spice",
        "--video", "virtio" if os_name != "windows" else "vga",
        "--osinfo", f"detect=on,name={os_variant}",
        "--noautoconsole",
    ]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False
        )
    except OSError as error:
        return {
            "success": False,
            "message": f"Could not execute virt-install: {error}",
            "command": command
        }

    if result.returncode != 0:
        error_message = result.stderr.strip() or result.stdout.strip()
        return {
            "success": False,
            "message": error_message or "virt-install failed.",
            "command": command
        }

    return {
        "success": True,
        "message": f"VM '{name}' was created successfully.",
        "command": command,
        "stdout": result.stdout.strip(),
        "os_variant": os_variant
    }
