"""Scan directories for VST3 plugins."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

# Common VST directories on Windows
DEFAULT_VST_PATHS = [
    os.path.expandvars(r"%PROGRAMFILES%\Common Files\VST3"),
    os.path.expandvars(r"%PROGRAMFILES(X86)%\Common Files\VST3"),
    os.path.expandvars(r"%LOCALAPPDATA%\Programs\Common Files\VST3"),
    os.path.expanduser("~/.vst3"),
]


@dataclass
class VSTPlugin:
    """Discovered VST3 plugin."""

    name: str
    path: str


def scan_vst_directory(directory: str) -> list[VSTPlugin]:
    """Scan a single directory for .vst3 files."""
    dir_path = Path(directory)
    if not dir_path.exists():
        return []

    plugins = []
    for vst3_file in dir_path.glob("*.vst3"):
        name = vst3_file.stem
        plugins.append(VSTPlugin(name=name, path=str(vst3_file)))

    return sorted(plugins, key=lambda p: p.name)


def scan_all_vst_directories(
    extra_paths: list[str] | None = None,
) -> list[VSTPlugin]:
    """Scan all known VST directories plus any extras."""
    paths = list(DEFAULT_VST_PATHS)
    if extra_paths:
        paths.extend(extra_paths)

    all_plugins: list[VSTPlugin] = []
    seen_paths: set[str] = set()

    for directory in paths:
        for plugin in scan_vst_directory(directory):
            if plugin.path not in seen_paths:
                seen_paths.add(plugin.path)
                all_plugins.append(plugin)

    return all_plugins


def load_vst_plugin(plugin_path: str):
    """Load a VST3 plugin via Pedalboard.

    Returns the loaded plugin object, or raises ImportError if pedalboard
    is not available.
    """
    try:
        from pedalboard import load_plugin

        return load_plugin(plugin_path)
    except ImportError:
        raise ImportError(
            "pedalboard is required for VST3 loading. "
            "Install with: pip install pedalboard"
        )
