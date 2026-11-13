"""CLI entry point and rendering."""
import argparse
import os
import sys
from concurrent.futures import ThreadPoolExecutor

from . import color, config
from . import core

if hasattr(sys.stdout, "reconfigure") and (sys.stdout.encoding or "").lower() not in ("utf-8", "utf8"):
    sys.stdout.reconfigure(errors="replace")  # legacy consoles (cp866/cp1251) can't encode █

_JOBS = {}  # filled in _gather(): provider-dependent


def _gather(provider, wanted: list[str]) -> dict[str, object]:
    jobs: dict[str, object] = {
        "username": core.username,
        "hostname": core.hostname,
        "os_name": provider.os_info,
        "kernel": provider.kernel_version,
        "py_version": core.python_version,
        "cpu": provider.cpu_info,
        "ram": provider.ram_usage,
        "uptime": provider.uptime,
    }
    extras = {
        "shell": {"shell_info": provider.shell_info},
        "mainboard": {"mb_name": provider.motherboard_name, "mb_vendor": provider.motherboard_vendor},
        "gpu": {"gpu": provider.gpu_info},
        "disks": {"disks": provider.disk_info},
        "locale": {"locale_info": provider.locale_info},
        "battery": {"battery": provider.battery_info},
    }
    for module in wanted:
        jobs.update(extras.get(module, {}))

    with ThreadPoolExecutor(max_workers=max(1, len(jobs))) as pool:
        futures = {key: pool.submit(fn) for key, fn in jobs.items()}
        return {key: future.result() for key, future in futures.items()}


def _hidden_disk(item: tuple[str, str, str], hidden: set[str]) -> bool:
    device, mount, _ = item
    if os.name == "nt":
        return device[:2].upper() in hidden or mount[:2].upper() in hidden
    return device in hidden or mount in hidden


def _render(info: dict, cfg: dict, no_color: bool):
    if no_color:
        label = lambda text: f"{text}{cfg['separator']}"  # noqa: E731
    else:
        accent = color.resolve(cfg["accent"])
        bold = "\033[1m" if cfg["bold"] else ""

        def label(text):
            return f"{accent}{bold}{text}\033[0m{cfg['separator']}"

    header = "" if no_color else color.resolve(cfg["accent"])
    header_bold = "\033[1m" if header and cfg["bold"] else ""

    print("")
    print(f"{header}{header_bold}{info['username']}@{info['hostname']}")
    print("=" * len(f"{info['username']}@{info['hostname']}"))

    print(f"{label('OS')}{info['os_name']}")
    print(f"{label('Kernel')}{info['kernel']}")

    if info.get("shell_info"):
        print(f"{label('Shell')}{info['shell_info']}")

    print(f"{label('Python Version')}{info['py_version']}")
    print(f"{label('Uptime')}{info['uptime']}")

    if info.get("mb_vendor") is not None:
        print(f"{label('Mainboard Vendor')}{info['mb_vendor']}")
    if info.get("mb_name") is not None:
        print(f"{label('Mainboard Model Name')}{info['mb_name']}")

    print(f"{label('CPU')}{info['cpu']}")

    if info.get("gpu") is not None:
        print(f"{label('GPU')}{info['gpu']}")

    print(f"{label('RAM')}{info['ram']}")

    hidden = set(cfg["hide_disks"])
    for item in info.get("disks", []):
        if not _hidden_disk(item, hidden):
            name = f"Disk ({item[0]})"
            print(f"{label(name)}{item[2]}")

    if info.get("locale_info") is not None:
        print(f"{label('Locale')}{info['locale_info']}")

    if info.get("battery") is not None:
        print(f"{label('Battery')}{info['battery']}")

    if cfg["show_swatch"] and not no_color:
        print("")
        for color_value in color.Colors:
            print(f"{color_value.value}███", end='')
        print()
        for color_value in color.IntenseColors:
            print(f"{color_value.value}███", end='')
        print()

    print("\n")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="yafetch", description="yet another fetch app")
    parser.add_argument("--config", help="path to config.toml (default: auto)")
    parser.add_argument("--no-color", action="store_true",
                        help="disable ANSI colors (also respects the NO_COLOR env var)")
    args = parser.parse_args(argv)

    no_color = args.no_color or bool(os.environ.get("NO_COLOR"))
    cfg = config.load(args.config)

    if core.provider is None:
        print(f"yafetch: unsupported platform: {core.SYSTEM}", file=sys.stderr)
        return 1

    info = _gather(core.provider, cfg["modules"])
    _render(info, cfg, no_color)
    return 0
