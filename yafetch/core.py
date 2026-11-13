"""Platform dispatch and helpers shared by all providers."""
import datetime
import getpass
import platform
import subprocess


def _detect_system() -> str:
    """Map platform.system() to "windows" or "linux".

    MSYS2/Cygwin Python builds report themselves as MSYS_NT*/CYGWIN_NT*/MINGW*_NT*
    but expose a POSIX view of the world, so they share the Linux provider.
    Other platforms, including macOS, are unsupported by design.
    """
    system = platform.system()
    if system == "Windows":
        return "windows"
    if system == "Linux" or system.startswith(("MSYS", "CYGWIN", "MINGW")):
        return "linux"
    return "unknown"


SYSTEM = _detect_system()


def _run(command: list[str]) -> str | None:
    """Run a command without a shell, return stripped stdout or None."""
    try:
        result = subprocess.run(command, capture_output=True)
    except OSError:
        return None
    if result.returncode != 0:
        return None
    return result.stdout.decode("utf-8", errors="replace").strip()


def _read_file(path: str) -> str | None:
    try:
        with open(path, encoding="utf-8", errors="replace") as handle:
            return handle.read().strip() or None
    except OSError:
        return None


def byte_convert(amount) -> str:
    if amount == 0:
        return "0 B"
    sizes = ["B", "KiB", "MiB", "GiB", "TiB", "PiB"]
    i = 0
    while amount >= 1024 and i < len(sizes) - 1:
        amount /= 1024
        i += 1
    return f"{amount:.2f} {sizes[i]}"


def format_uptime(seconds: float) -> str:
    secs = max(0, int(seconds))
    mins = secs % 3600 // 60
    hours = secs % (3600 * 24) // 3600
    days = secs // (3600 * 24)
    if days:
        return f"{days} d {hours} h {mins} min"
    if hours:
        return f"{hours} h {mins} min"
    return f"{mins} min"


def format_disk_stats(used: str, total: str, percent: float, fstype: str) -> str:
    return f"{used} / {total} ({percent:.1f}%) - {fstype}"


def username() -> str:
    return getpass.getuser()


def hostname() -> str:
    return platform.uname().node


def python_version() -> str:
    return platform.python_version()


if SYSTEM == "windows":
    from .platforms import windows as provider
elif SYSTEM == "linux":
    from .platforms import linux as provider
else:
    provider = None  # unsupported platform
