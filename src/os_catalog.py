OS_CATALOG = [
    {"id": "ubuntu", "name": "Ubuntu", "family": "linux", "logo": "ubuntu", "prefixes": ["ubuntu"]},
    {"id": "debian", "name": "Debian", "family": "linux", "logo": "debian", "prefixes": ["debian"]},
    {"id": "linuxmint", "name": "Linux Mint", "family": "linux", "logo": "mint", "prefixes": ["linuxmint", "ubuntu"]},
    {"id": "fedora", "name": "Fedora", "family": "linux", "logo": "fedora", "prefixes": ["fedora"]},
    {"id": "archlinux", "name": "Arch Linux", "family": "linux", "logo": "arch", "prefixes": ["archlinux", "arch"]},
    {"id": "manjaro", "name": "Manjaro", "family": "linux", "logo": "manjaro", "prefixes": ["manjaro", "archlinux"]},
    {"id": "kali", "name": "Kali Linux", "family": "linux", "logo": "kali", "prefixes": ["kali", "debian"]},
    {"id": "parrot", "name": "Parrot OS", "family": "linux", "logo": "parrot", "prefixes": ["parrot", "debian"]},
    {"id": "rocky", "name": "Rocky Linux", "family": "linux", "logo": "rocky", "prefixes": ["rocky"]},
    {"id": "almalinux", "name": "AlmaLinux", "family": "linux", "logo": "almalinux", "prefixes": ["almalinux", "alma"]},
    {"id": "centos", "name": "CentOS Stream", "family": "linux", "logo": "centos", "prefixes": ["centos-stream", "centos"]},
    {"id": "opensuse", "name": "openSUSE", "family": "linux", "logo": "opensuse", "prefixes": ["opensuse"]},
    {"id": "sles", "name": "SUSE Linux Enterprise", "family": "linux", "logo": "opensuse", "prefixes": ["sles"]},
    {"id": "alpine", "name": "Alpine Linux", "family": "linux", "logo": "alpine", "prefixes": ["alpinelinux", "alpine"]},
    {"id": "gentoo", "name": "Gentoo", "family": "linux", "logo": "gentoo", "prefixes": ["gentoo"]},
    {"id": "nixos", "name": "NixOS", "family": "linux", "logo": "nixos", "prefixes": ["nixos"]},
    {"id": "popos", "name": "Pop!_OS", "family": "linux", "logo": "popos", "prefixes": ["popos", "ubuntu"]},
    {"id": "elementary", "name": "elementary OS", "family": "linux", "logo": "elementary", "prefixes": ["elementary", "ubuntu"]},
    {"id": "zorin", "name": "Zorin OS", "family": "linux", "logo": "zorin", "prefixes": ["zorin", "ubuntu"]},
    {"id": "mxlinux", "name": "MX Linux", "family": "linux", "logo": "mxlinux", "prefixes": ["mxlinux", "debian"]},
    {"id": "endeavouros", "name": "EndeavourOS", "family": "linux", "logo": "endeavouros", "prefixes": ["endeavouros", "archlinux"]},
    {"id": "voidlinux", "name": "Void Linux", "family": "linux", "logo": "voidlinux", "prefixes": ["voidlinux", "void"]},
    {"id": "oraclelinux", "name": "Oracle Linux", "family": "linux", "logo": "oraclelinux", "prefixes": ["oraclelinux"]},
    {"id": "slackware", "name": "Slackware", "family": "linux", "logo": "slackware", "prefixes": ["slackware"]},
    {"id": "mageia", "name": "Mageia", "family": "linux", "logo": "mageia", "prefixes": ["mageia"]},
    {"id": "clearlinux", "name": "Clear Linux", "family": "linux", "logo": "clearlinux", "prefixes": ["clear-linux-os", "clearlinux"]},
    {"id": "tails", "name": "Tails", "family": "linux", "logo": "tails", "prefixes": ["tails", "debian"]},
    {"id": "qubes", "name": "Qubes OS", "family": "linux", "logo": "qubes", "prefixes": ["qubes"]},
    {"id": "windows10", "name": "Windows 10", "family": "windows", "logo": "windows", "prefixes": ["win10"]},
    {"id": "windows11", "name": "Windows 11", "family": "windows", "logo": "windows", "prefixes": ["win11"]},
    {"id": "windowsserver", "name": "Windows Server", "family": "windows", "logo": "windows", "prefixes": ["win2k25", "win2k22", "win2k19", "win2k16"]},
    {"id": "other-linux", "name": "Other Linux / Generic ISO", "family": "linux", "logo": "linux", "prefixes": []},
]

ALIASES = {
    "mint": "linuxmint",
    "windows": "windows11",
    "win10": "windows10",
    "win11": "windows11",
    "linux": "other-linux",
}


def get_os_options():
    return [item["name"] for item in OS_CATALOG]


def get_os_profile(value):
    normalized = str(value or "").strip().lower()
    normalized = ALIASES.get(normalized, normalized)

    for item in OS_CATALOG:
        if item["id"] == normalized or item["name"].lower() == normalized:
            return dict(item)

    return {
        "id": normalized or "other-linux",
        "name": str(value or "Other Linux / Generic ISO"),
        "family": "linux",
        "logo": "linux",
        "prefixes": [],
    }


def get_os_id(value):
    return get_os_profile(value)["id"]


def get_logo_key(value):
    return get_os_profile(value)["logo"]
