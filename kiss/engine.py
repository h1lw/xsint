"""KISS OSINT Engine.

Main engine for orchestrating OSINT scans across multiple services.
Uses the plugin system for modular scanner integration.
"""

import time
from typing import Any, Callable, Dict, List, Optional

import requests

from kiss.config import get_config
from kiss.constants import ScanStatus, ScanType
from kiss.models import ScanResult, ThreatLevel
from kiss.scanner.detectors import detect_input_type, extract_metadata
from kiss.utils.logging import get_logger

logger = get_logger(__name__)


class OSINTEngine:
    """Main OSINT scanning engine with plugin support."""

    def __init__(self):
        """Initialize the OSINT engine."""
        self.config = get_config()
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "KISS/2.0 (OSINT Tool)",
                "Accept": "application/json",
            }
        )
        self._last_request_time: Dict[str, float] = {}
        self._plugin_instances: Dict[str, Any] = {}
        self._registry = None
        self._plugins_initialized = False

    def _init_plugins(self):
        """Initialize the plugin system."""
        if self._plugins_initialized:
            return

        try:
            from kiss.plugins.registry import get_registry

            self._registry = get_registry()
            self._registry.discover_plugins()
            self._plugins_initialized = True
        except Exception as e:
            logger.warning(f"Failed to initialize plugins: {e}")
            self._plugins_initialized = True  # Don't retry

    def _get_plugin_instance(self, plugin_class):
        """Get or create a plugin instance."""
        name = plugin_class.get_metadata().name
        if name not in self._plugin_instances:
            self._plugin_instances[name] = plugin_class(self.config, self.session)
        return self._plugin_instances[name]

    def detect_input_type(self, target: str) -> Optional[str]:
        """Detect the type of input target."""
        return detect_input_type(target)

    def _scan_with_plugins(
        self,
        target: str,
        scan_type: str,
        progress_callback: Callable[[float], None],
    ) -> List[Dict[str, Any]]:
        """Execute scan using all applicable plugins.

        Args:
            target: The target to scan
            scan_type: The type of scan (IP, EMAIL, etc.)
            progress_callback: Progress callback function

        Returns:
            List of result dicts from all plugins
        """
        self._init_plugins()

        if not self._registry:
            return []

        results: List[Dict[str, Any]] = []

        # Get applicable plugins
        plugins = self._registry.get_by_scan_type(scan_type)

        # Filter to enabled plugins
        enabled_plugins = []
        for plugin_class in plugins:
            plugin_name = plugin_class.get_metadata().name
            if self.config.is_service_enabled(plugin_name):
                enabled_plugins.append(plugin_class)

        if not enabled_plugins:
            return results

        # Run each plugin
        total = len(enabled_plugins)
        for i, plugin_class in enumerate(enabled_plugins):
            try:
                plugin = self._get_plugin_instance(plugin_class)

                # Create sub-progress callback
                def sub_progress(val, idx=i, tot=total):
                    overall = (idx + val) / tot
                    progress_callback(overall)

                plugin_results = plugin.scan(target, scan_type, sub_progress)
                results.extend(plugin_results)

            except Exception as e:
                logger.debug(f"Plugin {plugin_class.get_metadata().name} failed: {e}")

        return results

    # === IP Scanning ===

    def scan_ip(
        self, target: str, progress_callback: Callable[[float], None]
    ) -> ScanResult:
        """Scan an IP address for intelligence."""
        result = ScanResult(
            scan_type=ScanType.IP,
            target=target,
            status=ScanStatus.RUNNING,
        )
        start_time = time.time()

        try:
            progress_callback(0.05)

            # Use plugin system
            plugin_results = self._scan_with_plugins(target, "IP", progress_callback)
            for row in plugin_results:
                # Convert threat_level string to enum if needed
                if "threat_level" in row and isinstance(row["threat_level"], str):
                    row["threat_level"] = ThreatLevel[row["threat_level"]]
                result.add_info(**row)

            # Add metadata
            metadata = extract_metadata(target, ScanType.IP.value)
            if metadata.get("is_private"):
                result.add_info(
                    "Network Type", "Private/Internal IP", source="Analysis"
                )
            else:
                result.add_info("Network Type", "Public IP", source="Analysis")

            progress_callback(1.0)
            result.status = ScanStatus.COMPLETED

        except Exception as e:
            logger.error(f"IP scan failed: {e}")
            result.status = ScanStatus.FAILED
            result.error_message = str(e)

        result.scan_duration = time.time() - start_time
        return result

    # === Email Scanning ===

    def scan_email(
        self, target: str, progress_callback: Callable[[float], None]
    ) -> ScanResult:
        """Scan an email address for intelligence."""
        result = ScanResult(
            scan_type=ScanType.EMAIL,
            target=target,
            status=ScanStatus.RUNNING,
        )
        start_time = time.time()

        try:
            progress_callback(0.05)

            # Use plugin system
            plugin_results = self._scan_with_plugins(target, "EMAIL", progress_callback)
            for row in plugin_results:
                if "threat_level" in row and isinstance(row["threat_level"], str):
                    row["threat_level"] = ThreatLevel[row["threat_level"]]
                result.add_info(**row)

            # Add metadata
            metadata = extract_metadata(target, ScanType.EMAIL.value)
            result.add_info(
                "Domain", metadata.get("domain", "unknown"), source="Analysis"
            )
            if metadata.get("is_common_provider"):
                result.add_info(
                    "Provider Type", "Common Email Provider", source="Analysis"
                )

            progress_callback(1.0)
            result.status = ScanStatus.COMPLETED

        except Exception as e:
            logger.error(f"Email scan failed: {e}")
            result.status = ScanStatus.FAILED
            result.error_message = str(e)

        result.scan_duration = time.time() - start_time
        return result

    # === Phone Scanning ===

    def scan_phone(
        self, target: str, progress_callback: Callable[[float], None]
    ) -> ScanResult:
        """Scan a phone number for intelligence."""
        result = ScanResult(
            scan_type=ScanType.PHONE,
            target=target,
            status=ScanStatus.RUNNING,
        )
        start_time = time.time()

        try:
            progress_callback(0.05)

            # Use plugin system
            plugin_results = self._scan_with_plugins(target, "PHONE", progress_callback)
            for row in plugin_results:
                if "threat_level" in row and isinstance(row["threat_level"], str):
                    row["threat_level"] = ThreatLevel[row["threat_level"]]
                result.add_info(**row)

            progress_callback(1.0)
            result.status = ScanStatus.COMPLETED

        except Exception as e:
            logger.error(f"Phone scan failed: {e}")
            result.status = ScanStatus.FAILED
            result.error_message = str(e)

        result.scan_duration = time.time() - start_time
        return result

    # === Username Scanning ===

    def scan_username(
        self, target: str, progress_callback: Callable[[float], None]
    ) -> ScanResult:
        """Scan a username across platforms."""
        result = ScanResult(
            scan_type=ScanType.USERNAME,
            target=target,
            status=ScanStatus.RUNNING,
        )
        start_time = time.time()

        try:
            progress_callback(0.05)

            # Clean username
            username = target.lstrip("@")

            # Use plugin system
            plugin_results = self._scan_with_plugins(
                username, "USERNAME", progress_callback
            )
            for row in plugin_results:
                if "threat_level" in row and isinstance(row["threat_level"], str):
                    row["threat_level"] = ThreatLevel[row["threat_level"]]
                result.add_info(**row)

            progress_callback(1.0)
            result.status = ScanStatus.COMPLETED

        except Exception as e:
            logger.error(f"Username scan failed: {e}")
            result.status = ScanStatus.FAILED
            result.error_message = str(e)

        result.scan_duration = time.time() - start_time
        return result

    # === Address Scanning ===

    def scan_address(
        self, target: str, progress_callback: Callable[[float], None]
    ) -> ScanResult:
        """Scan a physical address for geolocation."""
        result = ScanResult(
            scan_type=ScanType.ADDRESS,
            target=target,
            status=ScanStatus.RUNNING,
        )
        start_time = time.time()

        try:
            progress_callback(0.05)

            # Use plugin system
            plugin_results = self._scan_with_plugins(
                target, "ADDRESS", progress_callback
            )
            for row in plugin_results:
                if "threat_level" in row and isinstance(row["threat_level"], str):
                    row["threat_level"] = ThreatLevel[row["threat_level"]]
                result.add_info(**row)

            progress_callback(1.0)
            result.status = ScanStatus.COMPLETED

        except Exception as e:
            logger.error(f"Address scan failed: {e}")
            result.status = ScanStatus.FAILED
            result.error_message = str(e)

        result.scan_duration = time.time() - start_time
        return result

    # === Hash Scanning ===

    def scan_hash(
        self, target: str, progress_callback: Callable[[float], None]
    ) -> ScanResult:
        """Scan a password hash."""
        result = ScanResult(
            scan_type=ScanType.HASH,
            target=target,
            status=ScanStatus.RUNNING,
        )
        start_time = time.time()

        try:
            progress_callback(0.05)

            # Use plugin system
            plugin_results = self._scan_with_plugins(target, "HASH", progress_callback)
            for row in plugin_results:
                if "threat_level" in row and isinstance(row["threat_level"], str):
                    row["threat_level"] = ThreatLevel[row["threat_level"]]
                result.add_info(**row)

            progress_callback(1.0)
            result.status = ScanStatus.COMPLETED

        except Exception as e:
            logger.error(f"Hash scan failed: {e}")
            result.status = ScanStatus.FAILED
            result.error_message = str(e)

        result.scan_duration = time.time() - start_time
        return result

    # === Generic Scan Method ===

    def scan(
        self,
        target: str,
        scan_type: Optional[str] = None,
        progress_callback: Optional[Callable[[float], None]] = None,
    ) -> ScanResult:
        """Generic scan method that auto-detects type if not provided.

        Args:
            target: The target to scan
            scan_type: Optional scan type override
            progress_callback: Optional progress callback

        Returns:
            ScanResult with findings
        """
        if progress_callback is None:
            progress_callback = lambda x: None

        # Auto-detect type if not provided
        if scan_type is None:
            scan_type = self.detect_input_type(target)

        if scan_type is None:
            result = ScanResult(
                scan_type=ScanType.EMAIL,  # Default
                target=target,
                status=ScanStatus.FAILED,
            )
            result.error_message = "Could not detect input type"
            return result

        # Route to appropriate scan method
        scan_type_upper = scan_type.upper()

        if scan_type_upper == "IP":
            return self.scan_ip(target, progress_callback)
        elif scan_type_upper == "EMAIL":
            return self.scan_email(target, progress_callback)
        elif scan_type_upper == "PHONE":
            return self.scan_phone(target, progress_callback)
        elif scan_type_upper == "USERNAME":
            return self.scan_username(target, progress_callback)
        elif scan_type_upper == "ADDRESS":
            return self.scan_address(target, progress_callback)
        elif scan_type_upper == "HASH":
            return self.scan_hash(target, progress_callback)
        else:
            result = ScanResult(
                scan_type=ScanType.EMAIL,
                target=target,
                status=ScanStatus.FAILED,
            )
            result.error_message = f"Unsupported scan type: {scan_type}"
            return result

    def get_available_plugins(self) -> List[Dict[str, Any]]:
        """Get list of available plugins with their metadata.

        Returns:
            List of plugin info dicts
        """
        self._init_plugins()

        if not self._registry:
            return []

        plugins = []
        for name, plugin_class in self._registry.get_all().items():
            metadata = plugin_class.get_metadata()
            plugins.append(
                {
                    "name": metadata.name,
                    "display_name": metadata.display_name,
                    "description": metadata.description,
                    "category": metadata.category,
                    "scan_types": metadata.supported_scan_types,
                    "requires_api_key": len(metadata.api_key_requirements) > 0,
                    "is_enabled": self.config.is_service_enabled(metadata.name),
                }
            )

        return plugins


# Global engine instance
_engine_instance: Optional[OSINTEngine] = None


def get_engine() -> OSINTEngine:
    """Get the global OSINT engine instance."""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = OSINTEngine()
    return _engine_instance


def reset_engine() -> OSINTEngine:
    """Reset the engine instance (useful for testing)."""
    global _engine_instance
    _engine_instance = OSINTEngine()
    return _engine_instance
