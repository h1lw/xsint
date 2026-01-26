"""XSINT Configuration Management.

Handles configuration loading, validation, and management for the XSINT application.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

from kiss.constants import DEFAULT_CONFIG, DEFAULT_DIRS, API_ENDPOINTS, REQUEST_HEADERS
from kiss.models import APIKey, ServiceConfig

# Additional API endpoints for new modules
BREACH_API_ENDPOINTS = {
    "LEAKCHECK_API": "https://leakcheck.io/api/public",
    "SNUSBASE_API": "https://api.snusbase.com",
    "DEHASHED_API": "https://api.dehashed.com/search",
    "HASHES_ORG_API": "https://hashes.org/api.php",
    "HIBP_PASSWORDS_API": "https://api.pwnedpasswords.com/range",
    "NITRXGEN_API": "https://www.nitrxgen.net/md5db",
}


@dataclass
class KISSConfig:
    """Main configuration class for KISS."""

    # Basic settings
    max_concurrent_scans: int = DEFAULT_CONFIG["max_concurrent_scans"]
    request_timeout: int = DEFAULT_CONFIG["request_timeout"]
    rate_limit_delay: float = DEFAULT_CONFIG["rate_limit_delay"]
    max_retries: int = DEFAULT_CONFIG["max_retries"]
    cache_duration: int = DEFAULT_CONFIG["cache_duration"]
    log_level: str = DEFAULT_CONFIG["log_level"]

    # UI settings
    enable_animations: bool = DEFAULT_CONFIG["enable_animations"]
    default_theme: str = DEFAULT_CONFIG["default_theme"]

    # API keys
    api_keys: Dict[str, APIKey] = field(default_factory=dict)

    # Service configurations
    services: Dict[str, ServiceConfig] = field(default_factory=dict)

    # Directory paths
    config_dir: str = field(
        default_factory=lambda: str(Path(DEFAULT_DIRS["config"]).expanduser())
    )
    cache_dir: str = field(
        default_factory=lambda: str(Path(DEFAULT_DIRS["cache"]).expanduser())
    )
    logs_dir: str = field(
        default_factory=lambda: str(Path(DEFAULT_DIRS["logs"]).expanduser())
    )
    exports_dir: str = field(
        default_factory=lambda: str(Path(DEFAULT_DIRS["exports"]).expanduser())
    )

    # File paths
    config_file: str = field(init=False)

    def __post_init__(self):
        """Initialize paths and default configurations."""
        # Ensure directories exist
        self._ensure_directories()

        # Set config file path
        self.config_file = os.path.join(self.config_dir, "config.json")

        # Initialize default service configurations
        self._initialize_default_services()

        # Load environment variables for API keys
        self._load_env_api_keys()

    def _ensure_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        for directory in [
            self.config_dir,
            self.cache_dir,
            self.logs_dir,
            self.exports_dir,
        ]:
            Path(directory).mkdir(parents=True, exist_ok=True)

    def _initialize_default_services(self) -> None:
        """Initialize default service configurations."""
        default_services = {
            "hibp": ServiceConfig(
                name="HIBP",
                base_url=API_ENDPOINTS["HIBP_API"],
                timeout=30,
                max_retries=3,
                rate_limit=120,  # Official HIBP limit
                headers={
                    "User-Agent": REQUEST_HEADERS["User-Agent"],
                    "Accept": "application/json",
                    "hibp-api-key": "",  # Will be set from API key
                },
                is_enabled=True,
            ),
            "ipinfo": ServiceConfig(
                name="IPInfo",
                base_url=API_ENDPOINTS["IPINFO_API"],
                timeout=30,
                max_retries=3,
                rate_limit=1000,
                headers={
                    "User-Agent": REQUEST_HEADERS["User-Agent"],
                    "Accept": "application/json",
                    "Authorization": "",  # Will be set from API key
                },
                is_enabled=True,
            ),
            "gravatar": ServiceConfig(
                name="Gravatar",
                base_url=API_ENDPOINTS["GRATAR_API"],
                timeout=15,
                max_retries=2,
                rate_limit=60,
                headers={
                    "User-Agent": REQUEST_HEADERS["User-Agent"],
                    "Accept": "application/json",
                },
                is_enabled=True,
            ),
            "nominatim": ServiceConfig(
                name="Nominatim",
                base_url=API_ENDPOINTS["NOMINATIM_API"],
                timeout=30,
                max_retries=3,
                rate_limit=60,
                headers={
                    "User-Agent": REQUEST_HEADERS["User-Agent"],
                    "Accept": "application/json",
                },
                is_enabled=True,
            ),
            "hudson_rock": ServiceConfig(
                name="Hudson Rock",
                base_url=API_ENDPOINTS["HUDSON_ROCK_API"],
                timeout=30,
                max_retries=3,
                rate_limit=30,
                headers={
                    "User-Agent": REQUEST_HEADERS["User-Agent"],
                    "Accept": "application/json",
                },
                is_enabled=True,
            ),
            # Breach checking services
            "leakcheck": ServiceConfig(
                name="LeakCheck",
                base_url=BREACH_API_ENDPOINTS["LEAKCHECK_API"],
                timeout=30,
                max_retries=3,
                rate_limit=10,
                headers={
                    "User-Agent": REQUEST_HEADERS["User-Agent"],
                    "Accept": "application/json",
                },
                is_enabled=True,
            ),
            "snusbase": ServiceConfig(
                name="Snusbase",
                base_url=BREACH_API_ENDPOINTS["SNUSBASE_API"],
                timeout=30,
                max_retries=3,
                rate_limit=30,
                headers={
                    "User-Agent": REQUEST_HEADERS["User-Agent"],
                    "Accept": "application/json",
                    "Auth": "",  # Will be set from API key
                },
                is_enabled=True,
            ),
            "dehashed": ServiceConfig(
                name="DeHashed",
                base_url=BREACH_API_ENDPOINTS["DEHASHED_API"],
                timeout=30,
                max_retries=3,
                rate_limit=5,
                headers={
                    "User-Agent": REQUEST_HEADERS["User-Agent"],
                    "Accept": "application/json",
                },
                is_enabled=True,
            ),
            # Hash lookup services
            "hashes_org": ServiceConfig(
                name="Hashes.org",
                base_url=BREACH_API_ENDPOINTS["HASHES_ORG_API"],
                timeout=30,
                max_retries=3,
                rate_limit=30,
                headers={
                    "User-Agent": REQUEST_HEADERS["User-Agent"],
                    "Accept": "application/json",
                },
                is_enabled=True,
            ),
            "hibp_passwords": ServiceConfig(
                name="HIBP Passwords",
                base_url=BREACH_API_ENDPOINTS["HIBP_PASSWORDS_API"],
                timeout=15,
                max_retries=3,
                rate_limit=100,
                headers={
                    "User-Agent": REQUEST_HEADERS["User-Agent"],
                    "Accept": "text/plain",
                },
                is_enabled=True,
            ),
        }

        self.services.update(default_services)

    def _load_env_api_keys(self) -> None:
        """Load API keys from environment variables."""
        env_mappings = {
            "KISS_HIBP_API_KEY": "hibp",
            "KISS_IPINFO_API_KEY": "ipinfo",
            "KISS_GRAVATAR_API_KEY": "gravatar",
            "KISS_NOMINATIM_API_KEY": "nominatim",
            "KISS_HUDSON_ROCK_API_KEY": "hudson_rock",
        }

        for env_var, service_name in env_mappings.items():
            if env_var in os.environ:
                api_key_value = os.environ[env_var]
                if api_key_value:
                    self.set_api_key(service_name, api_key_value)

    def set_api_key(
        self, service_name: str, api_key_value: str, rate_limit: Optional[int] = None
    ) -> None:
        """Set an API key for a service."""
        if service_name in self.services:
            api_key = APIKey(
                name=f"{service_name}_key",
                key=api_key_value,
                service=service_name,
                rate_limit=rate_limit or self.services[service_name].rate_limit,
            )
            self.api_keys[service_name] = api_key

            # Update service configuration
            self.services[service_name].api_key = api_key

            # Update headers for specific services
            if service_name == "hibp":
                self.services[service_name].headers["hibp-api-key"] = api_key_value
            elif service_name == "ipinfo":
                self.services[service_name].headers["Authorization"] = (
                    f"Bearer {api_key_value}"
                )

    def get_api_key(self, service_name: str) -> Optional[str]:
        """Get API key for a service."""
        if service_name in self.api_keys:
            return self.api_keys[service_name].key
        return None

    def is_service_enabled(self, service_name: str) -> bool:
        """Check if a service is enabled."""
        if service_name in self.services:
            return self.services[service_name].is_enabled
        return False

    def enable_service(self, service_name: str) -> None:
        """Enable a service."""
        if service_name in self.services:
            self.services[service_name].is_enabled = True

    def disable_service(self, service_name: str) -> None:
        """Disable a service."""
        if service_name in self.services:
            self.services[service_name].is_enabled = False

    def load_from_file(self, config_file: Optional[str] = None) -> bool:
        """Load configuration from JSON file."""
        file_path = config_file or self.config_file

        if not os.path.exists(file_path):
            # Create default config file
            return self.save_to_file(file_path)

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                config_data = json.load(f)

            # Update simple configuration from file (skip complex objects)
            skip_keys = {"services", "api_keys"}
            for key, value in config_data.items():
                if (
                    key not in skip_keys
                    and hasattr(self, key)
                    and not key.startswith("_")
                ):
                    setattr(self, key, value)

            # Update service configurations from file (without overwriting objects)
            if "services" in config_data and isinstance(config_data["services"], dict):
                for name, service_data in config_data["services"].items():
                    if name in self.services and isinstance(service_data, dict):
                        # Update existing service object attributes
                        for attr_key, attr_value in service_data.items():
                            if hasattr(self.services[name], attr_key):
                                setattr(self.services[name], attr_key, attr_value)

            if "api_keys" in config_data and isinstance(config_data["api_keys"], dict):
                for name, key_data in config_data["api_keys"].items():
                    if isinstance(key_data, dict):
                        api_key = APIKey(**key_data)
                        self.api_keys[name] = api_key
                        # Update service reference
                        if api_key.service in self.services:
                            self.services[api_key.service].api_key = api_key

            return True

        except (json.JSONDecodeError, IOError, KeyError) as e:
            print(f"Error loading configuration: {e}")
            return False

    def save_to_file(self, config_file: Optional[str] = None) -> bool:
        """Save configuration to JSON file."""
        file_path = config_file or self.config_file

        try:
            # Convert configuration to dictionary
            config_dict = {
                "max_concurrent_scans": self.max_concurrent_scans,
                "request_timeout": self.request_timeout,
                "rate_limit_delay": self.rate_limit_delay,
                "max_retries": self.max_retries,
                "cache_duration": self.cache_duration,
                "log_level": self.log_level,
                "enable_animations": self.enable_animations,
                "default_theme": self.default_theme,
                "config_dir": self.config_dir,
                "cache_dir": self.cache_dir,
                "logs_dir": self.logs_dir,
                "exports_dir": self.exports_dir,
                "services": {},
                "api_keys": {},
            }

            # Convert services to dictionaries
            for name, service in self.services.items():
                service_dict = {
                    "name": service.name,
                    "base_url": service.base_url,
                    "timeout": service.timeout,
                    "max_retries": service.max_retries,
                    "rate_limit": service.rate_limit,
                    "headers": service.headers,
                    "is_enabled": service.is_enabled,
                }
                # Don't include full API key object in service config
                config_dict["services"][name] = service_dict

            # Convert API keys to dictionaries (without actual keys for security)
            for name, api_key in self.api_keys.items():
                key_dict = {
                    "name": api_key.name,
                    "service": api_key.service,
                    "rate_limit": api_key.rate_limit,
                    "last_used": api_key.last_used.isoformat()
                    if api_key.last_used
                    else None,
                    "is_active": api_key.is_active,
                    "metadata": api_key.metadata,
                    # Note: API key itself is stored separately for security
                }
                config_dict["api_keys"][name] = key_dict

            # Write to file
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)

            # Set appropriate file permissions (readable only by owner)
            os.chmod(file_path, 0o600)

            return True

        except (IOError, TypeError) as e:
            print(f"Error saving configuration: {e}")
            return False

    def get_service_config(self, service_name: str) -> Optional[ServiceConfig]:
        """Get service configuration."""
        return self.services.get(service_name)

    def list_enabled_services(self) -> List[str]:
        """Get list of enabled services."""
        try:
            return [
                name
                for name, service in self.services.items()
                if hasattr(service, "is_enabled") and service.is_enabled
            ]
        except Exception:
            # Fallback if services are not properly initialized
            return ["hibp", "ipinfo", "gravatar", "nominatim", "hudson_rock"]

    def get_rate_limit(self, service_name: str) -> int:
        """Get rate limit for a service."""
        if service_name in self.services:
            return self.services[service_name].rate_limit
        return DEFAULT_CONFIG["rate_limit_delay"]

    def validate_config(self) -> List[str]:
        """Validate configuration and return list of issues."""
        issues = []

        # Check if essential directories are accessible
        for directory in [
            self.config_dir,
            self.cache_dir,
            self.logs_dir,
            self.exports_dir,
        ]:
            if not os.path.exists(directory):
                try:
                    Path(directory).mkdir(parents=True, exist_ok=True)
                except PermissionError:
                    issues.append(f"Cannot create directory: {directory}")
            elif not os.access(directory, os.R_OK | os.W_OK):
                issues.append(f"No read/write access to directory: {directory}")

        # Check API keys for enabled services
        for name, service in self.services.items():
            if service.is_enabled and not self.get_api_key(name):
                # Only warn about API keys for services that typically need them
                if name in ["hibp", "ipinfo"]:
                    issues.append(
                        f"Service '{name}' is enabled but no API key is configured"
                    )

        # Validate numeric values
        if self.max_concurrent_scans < 1:
            issues.append("max_concurrent_scans must be at least 1")

        if self.request_timeout < 1:
            issues.append("request_timeout must be at least 1 second")

        if self.max_retries < 0:
            issues.append("max_retries cannot be negative")

        return issues


# Global configuration instance
_config_instance: Optional[KISSConfig] = None


def get_config() -> KISSConfig:
    """Get the global configuration instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = KISSConfig()
        _config_instance.load_from_file()
    return _config_instance


def reload_config() -> KISSConfig:
    """Reload configuration from file."""
    global _config_instance
    _config_instance = KISSConfig()
    _config_instance.load_from_file()
    return _config_instance


def reset_config() -> KISSConfig:
    """Reset configuration to defaults."""
    global _config_instance
    _config_instance = KISSConfig()
    _config_instance.load_from_file()
    return _config_instance
