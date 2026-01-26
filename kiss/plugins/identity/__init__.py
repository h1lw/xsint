"""Identity Lookup Plugins."""

from .gravatar import GravatarPlugin
from .nominatim import NominatimPlugin

__all__ = ["GravatarPlugin", "NominatimPlugin"]
