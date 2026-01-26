"""KISS API Key Manager.

Manages API key detection, status tracking, and dynamic menu generation
for the TUI settings interface.
"""

import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from .base import APIKeyRequirement
from .registry import get_registry


@dataclass
class APIKeyStatus:
    """Status of an API key configuration."""

    requirement: APIKeyRequirement
    is_configured: bool
    masked_value: Optional[str]  # e.g., "***1234"
    category: str
    plugin_name: str


class APIKeyManager:
    """Manages API key detection and status for dynamic menu generation."""

    # Category display order for consistent UI
    CATEGORY_ORDER = [
        "Breach Detection",
        "IP Intelligence",
        "Identity Lookup",
        "Hash Lookup",
        "Phone Intelligence",
        "Username Enumeration",
        "Custom",
    ]

    def __init__(self, config: Any):
        """Initialize the API key manager.

        Args:
            config: KISSConfig instance
        """
        self.config = config
        self.registry = get_registry()
        # Ensure plugins are discovered
        self.registry.discover_plugins()

    def get_all_api_keys_by_category(self) -> Dict[str, List[APIKeyStatus]]:
        """Get all API keys organized by category with status.

        Returns:
            Dict of category name to list of APIKeyStatus
        """
        requirements = self.registry.get_all_api_requirements()
        result: Dict[str, List[APIKeyStatus]] = {}

        # Process in category order
        for category in self.CATEGORY_ORDER:
            if category in requirements:
                result[category] = []
                for req in requirements[category]:
                    status = self._get_key_status(req, category)
                    result[category].append(status)

        # Add any categories not in the predefined order
        for category, reqs in requirements.items():
            if category not in result:
                result[category] = []
                for req in reqs:
                    status = self._get_key_status(req, category)
                    result[category].append(status)

        return result

    def _get_key_status(self, req: APIKeyRequirement, category: str) -> APIKeyStatus:
        """Get status for a single API key requirement.

        Args:
            req: The API key requirement
            category: The category name

        Returns:
            APIKeyStatus for the key
        """
        # Check config first
        key_value = None
        if hasattr(self.config, "get_api_key"):
            key_value = self.config.get_api_key(req.key_name.lower())

        # Then check environment
        if not key_value:
            key_value = os.environ.get(req.env_var)

        is_configured = bool(key_value)
        masked = None

        if key_value:
            if len(key_value) > 4:
                masked = "***" + key_value[-4:]
            else:
                masked = "****"

        # Find plugin name for this requirement
        plugin_name = ""
        for plugin_class in self.registry.get_all().values():
            metadata = plugin_class.get_metadata()
            for plugin_req in metadata.api_key_requirements:
                if plugin_req.key_name == req.key_name:
                    plugin_name = metadata.name
                    break

        return APIKeyStatus(
            requirement=req,
            is_configured=is_configured,
            masked_value=masked,
            category=category,
            plugin_name=plugin_name,
        )

    def get_menu_items(self) -> List[Tuple[str, str, str, bool, str, bool]]:
        """Generate menu items for TUI display.

        Returns:
            List of tuples: (display_name, key_name, category, is_configured,
                           masked_value, is_required)
        """
        all_keys = self.get_all_api_keys_by_category()
        items: List[Tuple[str, str, str, bool, str, bool]] = []

        for category in self.CATEGORY_ORDER:
            if category in all_keys:
                for status in all_keys[category]:
                    items.append(
                        (
                            status.requirement.display_name,
                            status.requirement.key_name,
                            category,
                            status.is_configured,
                            status.masked_value or "Not Set",
                            status.requirement.is_required,
                        )
                    )

        # Add items from categories not in predefined order
        for category, statuses in all_keys.items():
            if category not in self.CATEGORY_ORDER:
                for status in statuses:
                    items.append(
                        (
                            status.requirement.display_name,
                            status.requirement.key_name,
                            category,
                            status.is_configured,
                            status.masked_value or "Not Set",
                            status.requirement.is_required,
                        )
                    )

        return items

    def get_flat_items_with_headers(
        self,
    ) -> List[Tuple[str, Optional[str], Optional[str], bool, str, bool, bool]]:
        """Generate flat list with category headers for TUI.

        Returns:
            List of tuples: (display_text, key_name, category, is_configured,
                           masked_value, is_required, is_header)
            Headers have key_name=None and is_header=True
        """
        all_keys = self.get_all_api_keys_by_category()
        items: List[Tuple[str, Optional[str], Optional[str], bool, str, bool, bool]] = []

        for category in self.CATEGORY_ORDER:
            if category in all_keys and all_keys[category]:
                # Add category header
                items.append((category, None, category, False, "", False, True))

                # Add items
                for status in all_keys[category]:
                    items.append(
                        (
                            status.requirement.display_name,
                            status.requirement.key_name,
                            category,
                            status.is_configured,
                            status.masked_value or "Not Set",
                            status.requirement.is_required,
                            False,
                        )
                    )

        # Add categories not in predefined order
        for category, statuses in all_keys.items():
            if category not in self.CATEGORY_ORDER and statuses:
                items.append((category, None, category, False, "", False, True))
                for status in statuses:
                    items.append(
                        (
                            status.requirement.display_name,
                            status.requirement.key_name,
                            category,
                            status.is_configured,
                            status.masked_value or "Not Set",
                            status.requirement.is_required,
                            False,
                        )
                    )

        return items

    def set_api_key(self, key_name: str, value: str) -> bool:
        """Set an API key in config.

        Args:
            key_name: The key name (e.g., "hibp")
            value: The API key value

        Returns:
            True if saved successfully
        """
        if hasattr(self.config, "set_api_key"):
            self.config.set_api_key(key_name.lower(), value)

            if hasattr(self.config, "save_to_file"):
                return self.config.save_to_file()

        return False

    def get_unconfigured_count(self) -> int:
        """Get count of unconfigured required API keys.

        Returns:
            Number of missing required API keys
        """
        count = 0
        for category_keys in self.get_all_api_keys_by_category().values():
            for status in category_keys:
                if status.requirement.is_required and not status.is_configured:
                    count += 1
        return count

    def get_configured_count(self) -> int:
        """Get count of configured API keys.

        Returns:
            Number of configured API keys
        """
        count = 0
        for category_keys in self.get_all_api_keys_by_category().values():
            for status in category_keys:
                if status.is_configured:
                    count += 1
        return count

    def get_total_count(self) -> int:
        """Get total count of API keys.

        Returns:
            Total number of API keys
        """
        count = 0
        for category_keys in self.get_all_api_keys_by_category().values():
            count += len(category_keys)
        return count

    def get_key_info(self, key_name: str) -> Optional[APIKeyStatus]:
        """Get information about a specific API key.

        Args:
            key_name: The key name to look up

        Returns:
            APIKeyStatus or None if not found
        """
        for category_keys in self.get_all_api_keys_by_category().values():
            for status in category_keys:
                if status.requirement.key_name.lower() == key_name.lower():
                    return status
        return None

    def get_signup_url(self, key_name: str) -> Optional[str]:
        """Get signup URL for an API key.

        Args:
            key_name: The key name

        Returns:
            Signup URL or None
        """
        status = self.get_key_info(key_name)
        if status:
            return status.requirement.signup_url
        return None
