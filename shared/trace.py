"""Shared, color-aware trace helpers used by both agent implementations.

Each trace line is prefixed with a tag that is color-coded by role.
Colors are disabled automatically when stdout is not a TTY.
"""
import sys

_TTY = sys.stdout.isatty()

_RESET = "\033[0m" if _TTY else ""
_BOLD = "\033[1m" if _TTY else ""
_DIM = "\033[2m" if _TTY else ""

_COLORS = {
    "agent": "\033[36m",   # cyan
    "model": "\033[35m",   # magenta
    "tool":  "\033[33m",   # yellow
    "hitl":  "\033[32m",   # green
    "think": "\033[2m",    # dim
}

_DEFAULT = "\033[37m"  # light gray


def trace(tag: str, msg: str) -> None:
    """Print a single tagged trace line."""
    if _TTY:
        color = _COLORS.get(tag, _DEFAULT)
        print(f"  {color}[{tag:<5}]{_RESET} {msg}", flush=True)
    else:
        print(f"  [{tag:<5}] {msg}", flush=True)


def banner(title: str) -> None:
    """Print a bold banner — use at the start/end of an agent run."""
    bar = "═" * 72
    if _TTY:
        print(f"\n{_BOLD}{bar}{_RESET}\n{_BOLD}  {title}{_RESET}\n{_BOLD}{bar}{_RESET}", flush=True)
    else:
        print(f"\n{bar}\n  {title}\n{bar}", flush=True)


def separator(label: str = "") -> None:
    """Print a thin demarcation line — use between turns of the agent loop."""
    bar = "─" * 72
    line = f"{bar}  {label}" if label else bar
    if _TTY:
        print(f"{_DIM}{line}{_RESET}", flush=True)
    else:
        print(line, flush=True)
