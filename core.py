import subprocess
import psutil
import platform
import getpass
import datetime
import cpuinfo
import distro
import os

def byte_convert(amount):
    if amount == 0:
        return "0 B"
    sizes = ["B", 'KB', 'MB', 'GB', 'TB', 'PB']
    i = 0
    while amount >= 1024 and i < len(sizes)-1:
        amount /= 1024
        i += 1
    return f"{amount:.2f} {sizes[i]}"

def uptime():
    bt = psutil.boot_time()
    ut = datetime.datetime.now().timestamp() - bt
    mins = int(ut % 3600 // 60)
    hours = int(ut % (3600 * 24) // 3600)
    days = int(ut // (3600 * 24))
    if days:
        return f"{days} d {hours} h {mins} min"
    elif days == 0 and 24 > hours >= 1:
        return f"{hours} h {mins} min"
    elif hours == 0:
        return f"{mins} min"
    return None


def os_info():
    system = platform.system()
    if system == 'Windows':
        return f'{system} {platform.release()}'
    elif system == 'Darwin':
        return f"macOS {platform.mac_ver()}"
    elif system == "Linux":
        return distro.name(pretty=True)
    return None

def ram_usage():
    ram_stuff = psutil.virtual_memory()
    used = byte_convert(ram_stuff.used)
    total = byte_convert(ram_stuff.total)
    return f"{used} / {total} ({ram_stuff.percent}%)"

def username():
    return getpass.getuser()

def hostname():
    return platform.uname().node

def battery_info():
    battery_stuff = psutil.sensors_battery()
    if battery_stuff is not None:
        percents = f"{round(battery_stuff.percent)}%"
        if battery_stuff.power_plugged:
            return f"{percents} [AC Connected]"
        return f"{percents} [Discharging]"
    else:
        return None

def gpu_info():
    system = platform.system()
    if system == 'Windows':
        return subprocess.check_output("powershell -Command (Get-CimInstance Win32_VideoController).Name", shell=True).decode().strip()
    elif system == 'Linux':
        return subprocess.check_output("lspci | grep -i vga", shell=True).decode().split(':')[-1].strip()
    else:
        return None

def cpu_info():
    return f"{cpuinfo.get_cpu_info()['brand_raw']}"

def disk_info():
    parts = []
    for disk in psutil.disk_partitions():
        used = byte_convert(psutil.disk_usage(disk.mountpoint).used)
        total = byte_convert(psutil.disk_usage(disk.mountpoint).total)
        percent = psutil.disk_usage(disk.mountpoint).percent
        file_sys = disk.fstype
        parts.append(f"({disk.device})\033[0m: {used} / {total} ({percent}%) - {file_sys}")
    return parts

def kernel_version():
    system = platform.system()
    if system == "Linux":
        return platform.release()
    elif system == "Windows":
        return platform.win32_ver()[1]
    return None

def python_version():
    return platform.python_version()

def locale_info():
    import locale
    res = locale.getdefaultlocale()[0]
    return res

def motherboard_name():
    system = platform.system()
    if system == "Windows":
        return subprocess.check_output("powershell -Command (Get-WmiObject win32_baseboard).Product",
                                       shell=True).decode().strip()
    elif system == "Linux":
        return subprocess.check_output("cat /sys/devices/virtual/dmi/id/board_name", shell=True).decode().strip()
    return None

def motherboard_vendor():
    system = platform.system()
    if system == "Windows":
        return subprocess.check_output("powershell -Command (Get-WmiObject win32_baseboard).Manufacturer",
                                       shell=True).decode().strip()
    elif system == "Linux":
        return subprocess.check_output("cat /sys/devices/virtual/dmi/id/board_vendor", shell=True).decode().strip()
    return None

def shell_info():
    system = platform.system()
    if system == "Windows":
        return f"PowerShell {subprocess.check_output("powershell -Command $PSVersionTable.PSVersion.ToString()", shell=True).decode().strip()}"
    elif system == "Linux":
        return subprocess.check_output("$SHELL --version | head -n 1", shell=True).decode().strip()
    return None