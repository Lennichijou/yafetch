"""ANSI palette for yafetch."""
from enum import Enum


class Colors(Enum):
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'


class IntenseColors(Enum):
    BLACK = '\033[90m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'


PALETTE: dict[str, str] = {}
for _color in Colors:
    PALETTE[_color.name.lower()] = _color.value
for _color in IntenseColors:
    PALETTE[f"bright_{_color.name.lower()}"] = _color.value


def resolve(name: str) -> str:
    """ANSI code for a palette name, empty string if unknown."""
    return PALETTE.get((name or "").lower(), "")
