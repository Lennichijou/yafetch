import os
import subprocess
import psutil
import platform
import getpass
import datetime, time
import cpuinfo
import distro

def uptime():
    bt = datetime.datetime.fromtimestamp(psutil.boot_time())
    ut = (datetime.datetime.now() - bt)
    mins = ut.seconds % 3600 // 60
    hours = ut.seconds % (3600 * 24) // 3600
    days = ut.seconds // (3600 * 24)
    if days > 1:
        return f"{days} d {hours} h {mins} min"
    elif hours < 24:
        return f"{hours} h {mins} min"
    else:
        return f"{mins} min"

def os_info():
    system = platform.system()
    if system == 'Windows':
        return f'Windows {(platform.win32_ver()[0])}'
    elif system == 'Darwin':
        return platform.mac_ver()
    elif system == "Linux":
        return distro.name(pretty=True)
    return None

def ram_usage():
    ram_stuff = psutil.virtual_memory()
    return f"{round(ram_stuff.used / (2**30), 1)} / {round(ram_stuff.total / (2**30), 1)} GB ({ram_stuff.percent}%)"

def username():
    return getpass.getuser()

def hostname():
    return platform.uname().node

def battery_info():
    battery_stuff = psutil.sensors_battery()
    return f"{round(battery_stuff.percent)}%"

def gpu_info():
    system = platform.system()
    if system == 'Windows':
        return subprocess.check_output("powershell -Command (Get-CimInstance Win32_VideoController).Name", shell=True).decode().strip()
    elif system == 'Linux':
        return subprocess.check_output("lspci | grep -i vga", shell=True).decode().split(':')[-1].strip()
    else:
        return None

def cpu_info():
    return cpuinfo.get_cpu_info()['brand_raw']

def disk_info():
    parts = []
    for disk in psutil.disk_partitions():
        used = psutil.disk_usage(disk.mountpoint).used // (2 ** 30)
        total = psutil.disk_usage(disk.mountpoint).total // (2 ** 30)
        percent = psutil.disk_usage(disk.mountpoint).percent
        parts.append(f"\033[1mDisk {disk.device}\033[0m: {used} / {total} GB ({percent}%)")
    return parts

def kernel_version():
    return platform.release()

def python_version():
    return platform.python_version()

