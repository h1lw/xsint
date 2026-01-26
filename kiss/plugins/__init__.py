"""KISS Plugin System.

Modular plugin architecture for OSINT scanning services.
Plugins are auto-discovered from this package and from ~/.xsint/plugins/
"""

from .base import BasePlugin, PluginMetadata, APIKeyRequirement
from .registry import PluginRegistry, get_registry
from .manager import APIKeyManager

__all__ = [
    "BasePlugin",
    "PluginMetadata",
    "APIKeyRequirement",
    "PluginRegistry",
    "get_registry",
    "APIKeyManager",
]
