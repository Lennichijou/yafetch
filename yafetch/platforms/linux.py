"""Linux (and MSYS2/Cygwin) provider: /proc, /sys and friends."""
import os
import platform
import shutil

from .. import core


def _os_release() -> dict[str, str]:
    fields = {}
    text = core._read_file("/etc/os-release")
    if text:
        for line in text.splitlines():
            key, sep, value = line.partition("=")
            if sep:
                fields[key.strip()] = value.strip().strip('"')
    return fields


def os_info() -> str | None:
    pretty = _os_release().get("PRETTY_NAME")
    if pretty:
        return pretty
    uname = os.uname()
    return f"{uname.sysname} {uname.release}"


def kernel_version() -> str | None:
    return platform.release()


def cpu_info() -> str | None:
    text = core._read_file("/proc/cpuinfo")
    if not text:
        return None
    for line in text.splitlines():
        key, sep, value = line.partition(":")
        if sep and key.strip() in ("model name", "Model Name", "Hardware", "Model"):
            return value.strip()
    return None


def ram_usage() -> str | None:
    text = core._read_file("/proc/meminfo")
    if not text:
        return None
    fields: dict[str, int] = {}
    for line in text.splitlines():
        key, _, rest = line.partition(":")
        if rest.strip():
            fields[key.strip()] = int(rest.strip().split()[0])
    total = fields.get("MemTotal", 0)
    if not total:
        return None
    available = fields.get("MemAvailable", fields.get("MemFree", 0))
    used = (total - available) * 1024
    return f"{core.byte_convert(used)} / {core.byte_convert(total * 1024)} ({used / (total * 1024) * 100:.1f}%)"


def uptime() -> str | None:
    text = core._read_file("/proc/uptime")
    if not text:
        return None
    return core.format_uptime(float(text.split()[0]))


def battery_info() -> str | None:
    try:
        supplies = sorted(os.listdir("/sys/class/power_supply"))
    except OSError:
        return None
    for name in supplies:
        base = f"/sys/class/power_supply/{name}"
        if core._read_file(f"{base}/type") != "Battery":
            continue
        capacity = core._read_file(f"{base}/capacity")
        if not capacity:
            continue
        status = (core._read_file(f"{base}/status") or "Unknown").lower()
        percents = f"{capacity}%"
        if status in ("charging", "full"):
            return f"{percents} [AC Connected]"
        if status == "discharging":
            return f"{percents} [Discharging]"
        return f"{percents} [Unknown state]"
    return None


_PHYSICAL_FS = {
    "ext2", "ext3", "ext4", "xfs", "btrfs", "zfs", "f2fs", "jfs",
    "reiserfs", "bcachefs", "vfat", "exfat", "ntfs", "ntfs3", "fuseblk",
}


def disk_info() -> list[tuple[str, str, str]]:
    parts = []
    seen: set[str] = set()
    text = core._read_file("/proc/mounts") or ""
    for line in text.splitlines():
        fields = line.split()
        if len(fields) < 3:
            continue
        device, mount, fstype = fields[0], fields[1].replace("\\040", " "), fields[2]
        if fstype not in _PHYSICAL_FS or not device.startswith("/dev"):
            continue
        if mount in seen:
            continue
        try:
            usage = shutil.disk_usage(mount)
        except OSError:
            continue
        if usage.total == 0:
            continue
        seen.add(mount)
        percent = usage.used / usage.total * 100
        text_fmt = core.format_disk_stats(
            core.byte_convert(usage.used), core.byte_convert(usage.total),
            percent, fstype,
        )
        parts.append((device, mount, text_fmt))
    return parts


def gpu_info() -> str | None:
    raw = core._run(["lspci", "-d", "::0300"])
    if not raw:
        return None
    gpus = [line.split(": ", 1)[-1].strip() for line in raw.splitlines() if ": " in line]
    return ", ".join(gpus) or None


def motherboard_name() -> str | None:
    return core._read_file("/sys/devices/virtual/dmi/id/board_name")


def motherboard_vendor() -> str | None:
    return core._read_file("/sys/devices/virtual/dmi/id/board_vendor")


def shell_info() -> str | None:
    shell = os.environ.get("SHELL")
    if not shell:
        return None
    output = core._run([shell, "--version"])
    if output:
        return output.splitlines()[0]
    return None


def locale_info() -> str | None:
    name = os.environ.get("LC_ALL") or os.environ.get("LANG") or ""
    return name.partition(".")[0] or None
