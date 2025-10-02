import core
from color import Colors, IntenseColors

def main():

    header_color = Colors.MAGENTA.value
    username = core.username()
    hostname = core.hostname()
    os_name = core.os_info()
    kernel = core.kernel_version()
    py_version = core.python_version()
    cpu = core.cpu_info()
    gpu = core.gpu_info()
    battery = core.battery_info()
    locale_info = core.locale_info()
    ram = core.ram_usage()
    uptime = core.uptime()
    mb_name = core.motherboard_name()
    mb_vendor = core.motherboard_vendor()

    print("")

    print(f"{header_color}\033[1m{username}@{hostname}")

    print(f"{header_color}\033[1mOS\033[0m: {os_name}")

    print(f"{header_color}\033[1mKernel\033[0m: {kernel}")

    print(f"{header_color}\033[1mPython Version\033[0m: {py_version}")

    print(f"{header_color}\033[1mUptime\033[0m: {uptime}")

    if mb_vendor is not None:
        print(f"{header_color}\033[1mMainboard Vendor\033[0m: {mb_vendor}")

    if mb_vendor is not None:
        print(f"{header_color}\033[1mMainboard Model Name\033[0m: {mb_name}")

    print(f"{header_color}\033[1mCPU\033[0m: {cpu}")

    if gpu is not None:
        print(f"{header_color}\033[1mGPU\033[0m: {gpu}")

    print(f"{header_color}\033[1mRAM\033[0m: {ram}")

    for part in core.disk_info():
        print(f"{header_color}\033[1mDisk {part}", sep='\n')

    if locale_info is not None:
        print(f"{header_color}\033[1mLocale\033[0m: {locale_info}")

    if battery is not None:
        print(f"{header_color}\033[1mBattery\033[0m: {battery}")

    for color in Colors:
        print(f"{color.value}███",end='')

    print()

    for color in IntenseColors:
        print(f"{color.value}███", end='')

    print("\n")

if __name__ == "__main__":
    main()