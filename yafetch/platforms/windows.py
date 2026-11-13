"""Windows provider: registry + WinAPI via ctypes, no subprocess by default."""
import ctypes
import platform
import shutil
import winreg
from ctypes import wintypes
from functools import cache

from .. import core

_k32 = ctypes.windll.kernel32

_DISPLAY_CLASS = r"SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}"
_BIOS_KEY = r"HARDWARE\DESCRIPTION\System\BIOS"
_POWERSHELL_KEY = r"SOFTWARE\Microsoft\PowerShell\3\PowerShellEngine"

_CENTRAL_CPU_KEY = r"HARDWARE\DESCRIPTION\System\CentralProcessor\0"


def _registry_string(root: int, path: str, value_name: str) -> str | None:
    try:
        with winreg.OpenKey(root, path) as key:
            value, _ = winreg.QueryValueEx(key, value_name)
    except OSError:
        return None
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


# --- optional fallback: one PowerShell process when registry misses hardware ---

POWERSHELL_ARGS = ["powershell", "-NoProfile", "-NonInteractive", "-Command"]
_CIM_KEYS = ("GPU", "VENDOR", "PRODUCT")
_CIM_SCRIPT = (
    "$ErrorActionPreference = 'SilentlyContinue'; "
    "$gpu = (Get-CimInstance Win32_VideoController).Name -join ', '; "
    "$board = Get-CimInstance Win32_BaseBoard; "
    "Write-Output ('GPU::|::' + $gpu); "
    "Write-Output ('VENDOR::|::' + $board.Manufacturer); "
    "Write-Output ('PRODUCT::|::' + $board.Product)"
)
_cim_cache: dict[str, str] | None = None


def _cim() -> dict[str, str]:
    global _cim_cache
    if _cim_cache is None:
        _cim_cache = {}
        raw = core._run(POWERSHELL_ARGS + [_CIM_SCRIPT])
        if raw:
            for line in raw.splitlines():
                if "::|::" in line:
                    key, _, value = line.partition("::|::")
                    if key in _CIM_KEYS:
                        _cim_cache[key] = value
    return _cim_cache


# --- hardware ---


@cache
def cpu_info() -> str | None:
    return _registry_string(winreg.HKEY_LOCAL_MACHINE, _CENTRAL_CPU_KEY, "ProcessorNameString")


def gpu_info() -> str | None:
    names = []
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, _DISPLAY_CLASS) as cls:
            index = 0
            while True:
                try:
                    subkey = winreg.EnumKey(cls, index)
                    index += 1
                except OSError:
                    break
                name = _registry_string(
                    winreg.HKEY_LOCAL_MACHINE, rf"{_DISPLAY_CLASS}\{subkey}", "DriverDesc"
                )
                if name:
                    names.append(name)
    except OSError:
        names = []
    if names:
        return ", ".join(names)
    return _cim().get("GPU") or None


def motherboard_vendor() -> str | None:
    vendor = _registry_string(winreg.HKEY_LOCAL_MACHINE, _BIOS_KEY, "BaseBoardManufacturer")
    if vendor:
        return vendor
    return _cim().get("VENDOR") or None


def motherboard_name() -> str | None:
    product = _registry_string(winreg.HKEY_LOCAL_MACHINE, _BIOS_KEY, "BaseBoardProduct")
    if product:
        return product
    return _cim().get("PRODUCT") or None


# --- system state via WinAPI ---


class _MEMORYSTATUSEX(ctypes.Structure):
    _fields_ = [
        ("dwLength", ctypes.c_uint32),
        ("dwMemoryLoad", ctypes.c_uint32),
        ("ullTotalPhys", ctypes.c_ulonglong),
        ("ullAvailPhys", ctypes.c_ulonglong),
        ("ullTotalPageFile", ctypes.c_ulonglong),
        ("ullAvailPageFile", ctypes.c_ulonglong),
        ("ullTotalVirtual", ctypes.c_ulonglong),
        ("ullAvailVirtual", ctypes.c_ulonglong),
        ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
    ]


class _SYSTEM_POWER_STATUS(ctypes.Structure):
    _fields_ = [
        ("ACLineStatus", ctypes.c_ubyte),
        ("BatteryFlag", ctypes.c_ubyte),
        ("BatteryLifePercent", ctypes.c_ubyte),
        ("Reserved1", ctypes.c_ubyte),
        ("BatteryLifeTime", ctypes.c_uint32),
        ("BatteryFullLifeTime", ctypes.c_uint32),
    ]


def os_info() -> str:
    return f"{platform.system()} {platform.release()}"


def kernel_version() -> str:
    return platform.win32_ver()[1]


def uptime() -> str:
    return core.format_uptime(_k32.GetTickCount64() / 1000)


def ram_usage() -> str:
    status = _MEMORYSTATUSEX()
    status.dwLength = ctypes.sizeof(status)
    _k32.GlobalMemoryStatusEx(ctypes.byref(status))
    total = status.ullTotalPhys
    used = total - status.ullAvailPhys
    percent = used / total * 100 if total else 0.0
    return f"{core.byte_convert(used)} / {core.byte_convert(total)} ({percent:.1f}%)"


def battery_info() -> str | None:
    status = _SYSTEM_POWER_STATUS()
    if not _k32.GetSystemPowerStatus(ctypes.byref(status)):
        return None
    if status.BatteryFlag & 0x80 or status.BatteryLifePercent == 255:
        return None  # no battery
    percents = f"{status.BatteryLifePercent}%"
    if status.ACLineStatus == 1:
        return f"{percents} [AC Connected]"
    if status.ACLineStatus == 0:
        return f"{percents} [Discharging]"
    return f"{percents} [Unknown state]"


# --- disks ---

_DRIVE_TYPES = {2, 3, 5}  # removable, fixed, cdrom; network drives are skipped (slow)


def _logical_drives() -> list[str]:
    buf = ctypes.create_unicode_buffer(512)
    length = _k32.GetLogicalDriveStringsW(len(buf), buf)
    return [item for item in ctypes.wstring_at(buf, length).split("\x00") if item]


def _fs_type(root: str) -> str:
    name = ctypes.create_unicode_buffer(64)
    ok = _k32.GetVolumeInformationW(
        ctypes.c_wchar_p(root), None, 0, None, None, None, name, len(name)
    )
    return (name.value or "unknown") if ok else "unknown"


def disk_info() -> list[tuple[str, str, str]]:
    parts = []
    for root in _logical_drives():
        if _k32.GetDriveTypeW(ctypes.c_wchar_p(root)) not in _DRIVE_TYPES:
            continue
        try:
            usage = shutil.disk_usage(root)
        except OSError:
            continue
        if usage.total == 0:
            continue
        percent = usage.used / usage.total * 100
        text = core.format_disk_stats(
            core.byte_convert(usage.used), core.byte_convert(usage.total),
            percent, _fs_type(root),
        )
        parts.append((root, root, text))
    return parts


# --- shell and locale ---


class _PROCESSENTRY32W(ctypes.Structure):
    _fields_ = [
        ("dwSize", wintypes.DWORD),
        ("cntUsage", wintypes.DWORD),
        ("th32ProcessID", wintypes.DWORD),
        ("th32DefaultHeapID", ctypes.c_size_t),
        ("th32ModuleID", wintypes.DWORD),
        ("cntThreads", wintypes.DWORD),
        ("th32ParentProcessID", wintypes.DWORD),
        ("pcPriClassBase", ctypes.c_long),
        ("dwFlags", wintypes.DWORD),
        ("szExeFile", ctypes.c_wchar * 260),
    ]


def _parent_process_name() -> str | None:
    entry = _PROCESSENTRY32W()
    entry.dwSize = ctypes.sizeof(entry)
    TH32CS_SNAPPROCESS = 2
    INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value
    snapshot = _k32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    if snapshot == INVALID_HANDLE_VALUE or not snapshot:
        return None
    table: dict[int, tuple[int, str]] = {}
    try:
        ok = _k32.Process32FirstW(snapshot, ctypes.byref(entry))
        while ok:
            table[entry.th32ProcessID] = (entry.th32ParentProcessID, entry.szExeFile)
            ok = _k32.Process32NextW(snapshot, ctypes.byref(entry))
    finally:
        _k32.CloseHandle(snapshot)
    info = table.get(_k32.GetCurrentProcessId())
    parent = table.get(info[0]) if info else None
    return parent[1] if parent else None


def shell_info() -> str | None:
    parent = _parent_process_name()
    if not parent:
        return None
    name = parent[:-4] if parent.lower().endswith(".exe") else parent
    if name == "powershell":
        version = _registry_string(winreg.HKEY_LOCAL_MACHINE, _POWERSHELL_KEY, "PowerShellVersion")
        return f"PowerShell {version}" if version else None
    if name == "pwsh":
        return core._run(["pwsh", "--version"])
    if name in ("cmd", "bash", "zsh", "fish", "nu"):
        return name
    return None


def locale_info() -> str | None:
    name = ctypes.create_unicode_buffer(85)  # LOCALE_NAME_MAX_LENGTH
    if _k32.GetUserDefaultLocaleName(name, len(name)):
        return name.value or None
    return None
