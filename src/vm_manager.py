import re
import shutil
import subprocess
from pathlib import Path

from os_catalog import get_os_profile

RUNNING_STATES = {"running", "executando"}
STOPPED_STATES = {"shut off", "desligado", "desligada"}


def run_virsh_command(command_args):
    command = ["virsh", "--connect", "qemu:///system"] + command_args
    try:
        return subprocess.run(command, capture_output=True, text=True)
    except FileNotFoundError:
        return subprocess.CompletedProcess(
            command,
            127,
            stdout="",
            stderr="virsh executable was not found in PATH.",
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
        if len(parts) != 2 or parts[0] != "actual":
            continue
        try:
            memory_kib = int(parts[1])
        except ValueError:
            return None
        return f"{memory_kib / 1024 / 1024:.2f} GB"
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
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def get_vm_snapshot(vm_name):
    status = get_vm_status(vm_name)
    if status is None:
        return None

    return {
        "name": vm_name,
        "status": status,
        "vcpus": get_vm_vcpus(vm_name),
        "ram": get_vm_ram(vm_name),
        "ip": get_vm_ip(vm_name) if status.strip().lower() in RUNNING_STATES else None,
    }


def get_all_vms_info():
    result = []
    for vm_name in list_vms():
        snapshot = get_vm_snapshot(vm_name)
        if snapshot is not None:
            result.append(snapshot)
    return result


def get_available_os_variants():
    commands = [
        ["virt-install", "--osinfo", "list"],
        ["osinfo-query", "os", "--fields", "short-id"],
    ]

    for command in commands:
        if shutil.which(command[0]) is None:
            continue
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=False)
        except OSError:
            continue
        if result.returncode != 0:
            continue

        variants = set()
        for raw_line in result.stdout.splitlines():
            line = raw_line.strip()
            if not line or line.lower().startswith("short id") or set(line) == {"-"}:
                continue
            value = line.split()[0]
            if re.fullmatch(r"[A-Za-z0-9._+-]+", value):
                variants.add(value)
        if variants:
            return sorted(variants)

    return []


def _select_os_variant(os_name):
    profile = get_os_profile(os_name)
    available = get_available_os_variants()
    if not available:
        return None

    lowered = [(item, item.lower()) for item in available]
    for prefix in profile.get("prefixes", []):
        matches = [item for item, low in lowered if low == prefix or low.startswith(prefix)]
        if matches:
            return sorted(matches, reverse=True)[0]
    return None


def create_vm(name, os_name, vcpus, ram_gb, disk_gb, iso_path):
    name = str(name or "").strip()
    profile = get_os_profile(os_name)
    iso = Path(str(iso_path or "")).expanduser()

    if not name:
        return {"success": False, "message": "VM name cannot be empty."}

    if not re.fullmatch(r"[A-Za-z0-9._-]+", name):
        return {
            "success": False,
            "message": "VM name may contain only letters, numbers, '.', '_' and '-'.",
        }

    if get_vm_status(name) is not None:
        return {"success": False, "message": f"A VM named '{name}' already exists."}

    try:
        vcpus = int(vcpus)
        ram_gb = int(ram_gb)
        disk_gb = int(disk_gb)
    except (TypeError, ValueError):
        return {
            "success": False,
            "message": "vCPU, RAM and disk size must be whole numbers.",
        }

    if not 1 <= vcpus <= 64:
        return {"success": False, "message": "vCPU must be between 1 and 64."}
    if not 1 <= ram_gb <= 512:
        return {"success": False, "message": "RAM must be between 1 and 512 GB."}
    if not 1 <= disk_gb <= 4096:
        return {"success": False, "message": "Disk size must be between 1 and 4096 GB."}
    if not iso.is_file():
        return {"success": False, "message": f"ISO file was not found: {iso}"}
    if shutil.which("virt-install") is None:
        return {
            "success": False,
            "message": "virt-install was not found in PATH.",
        }

    family = profile.get("family", "linux")
    os_variant = _select_os_variant(profile["id"])
    memory_mb = ram_gb * 1024

    disk_bus = "sata" if family == "windows" else "virtio"
    network_model = "e1000e" if family == "windows" else "virtio"
    video_model = "vga" if family == "windows" else "virtio"

    osinfo_value = (
        f"detect=on,name={os_variant}"
        if os_variant
        else "detect=on,require=off"
    )

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
        "--video", video_model,
        "--osinfo", osinfo_value,
        "--noautoconsole",
    ]

    try:
        result = subprocess.run(command, capture_output=True, text=True, check=False)
    except OSError as error:
        return {
            "success": False,
            "message": f"Could not execute virt-install: {error}",
            "command": command,
        }

    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "virt-install failed."
        return {"success": False, "message": message, "command": command}

    return {
        "success": True,
        "message": f"VM '{name}' was created successfully.",
        "command": command,
        "stdout": result.stdout.strip(),
        "os_variant": os_variant,
        "os_profile": profile["id"],
    }
