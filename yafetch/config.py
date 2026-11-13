"""Config defaults, TOML loading and validation."""
import os
import sys
import tomllib
from pathlib import Path

from .color import PALETTE

ALL_MODULES = [
    "os", "kernel", "shell", "python", "uptime", "mainboard",
    "cpu", "gpu", "ram", "disks", "locale", "battery",
]

DEFAULTS = {
    "accent": "magenta",
    "bold": True,
    "separator": ": ",
    "modules": ALL_MODULES,
    "hide_disks": [],
    "show_swatch": True,
}


def config_path(explicit: str | None) -> Path | None:
    if explicit:
        return Path(explicit)
    override = os.environ.get("YAFETCH_CONFIG")
    if override:
        return Path(override)
    if os.name == "nt":
        return Path(os.environ.get("APPDATA", "~")).expanduser() / "yafetch" / "config.toml"
    xdg = os.environ.get("XDG_CONFIG_HOME")
    base = Path(xdg) if xdg else Path.home() / ".config"
    return base / "yafetch" / "config.toml"


def load(explicit: str | None) -> dict:
    cfg = dict(DEFAULTS)
    cfg["modules"] = list(ALL_MODULES)
    cfg["hide_disks"] = []
    path = config_path(explicit)
    if path is None:
        return cfg
    try:
        raw = tomllib.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        if explicit or os.environ.get("YAFETCH_CONFIG"):
            print(f"yafetch: config not found: {path}", file=sys.stderr)
        return cfg
    except tomllib.TOMLDecodeError as exc:
        print(f"yafetch: bad config {path}: {exc}", file=sys.stderr)
        return cfg

    accent = raw.get("accent")
    if accent is None:
        pass
    elif isinstance(accent, str) and accent.lower() in PALETTE:
        cfg["accent"] = accent.lower()
    else:
        print(f"yafetch: unknown color '{accent}', expected one of: {', '.join(PALETTE)}",
              file=sys.stderr)

    bold = raw.get("bold")
    if isinstance(bold, bool):
        cfg["bold"] = bold

    separator = raw.get("separator")
    if isinstance(separator, str):
        cfg["separator"] = separator

    swatch = raw.get("show_swatch")
    if isinstance(swatch, bool):
        cfg["show_swatch"] = swatch

    modules = raw.get("modules")
    if isinstance(modules, list):
        unknown = [m for m in modules if not isinstance(m, str) or m not in ALL_MODULES]
        if unknown:
            print(f"yafetch: unknown modules ignored: {', '.join(map(str, unknown))}; "
                  f"valid: {', '.join(ALL_MODULES)}", file=sys.stderr)
        wanted = {m for m in modules if isinstance(m, str) and m in ALL_MODULES}
        cfg["modules"] = [m for m in ALL_MODULES if m in wanted]

    hide_disks = raw.get("hide_disks")
    if isinstance(hide_disks, list):
        cfg["hide_disks"] = [str(item) for item in hide_disks]
        if os.name == "nt":
            cfg["hide_disks"] = [item.upper() for item in cfg["hide_disks"]]

    return cfg
