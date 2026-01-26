"""KISS Plugin Template.

This is a template for creating new KISS plugins.
Copy this file and modify it for your specific needs.
"""

from typing import Any, Callable, Dict, List, Optional
from kiss.plugins.async_base import AsyncBasePlugin, PluginMetadata, APIKeyRequirement


class YourPluginTemplate(AsyncBasePlugin):
    """Template plugin demonstrating the KISS plugin structure.

    Plugin Template:
    - Follow this structure for all new plugins
    - Use async methods for better performance
    - Implement proper error handling
    - Follow KISS naming conventions
    - Include comprehensive metadata
    """

    @classmethod
    def get_metadata(cls) -> PluginMetadata:
        """Return plugin metadata. MUST be implemented by all plugins.

        This metadata is used for:
        - Plugin discovery and registration
        - UI display and organization
        - API key management
        - Rate limiting and timeout configuration
        - Dependency management

        Returns:
            PluginMetadata instance with complete plugin information
        """
        return PluginMetadata(
            # Unique identifier (lowercase, no spaces)
            name="your_plugin_name",
            # Human-readable name (can have spaces, capitalization)
            display_name="Your Plugin Display Name",
            # Brief description of what the plugin does
            description="Brief description of plugin functionality",
            # Semantic version (major.minor.patch)
            version="1.0.0",
            # Category for organization in UI
            category="Your Category",
            # Supported scan types (must match ScanType enum)
            supported_scan_types=["EMAIL", "PHONE", "IP"],  # Add as needed
            # API key requirements (remove if no API needed)
            api_key_requirements=[
                APIKeyRequirement(
                    key_name="api_name",  # Internal key name
                    env_var="KISS_API_NAME_API_KEY",  # Environment variable
                    display_name="API Service Name API Key",  # Human readable
                    description="Required for accessing API Service Name",  # Purpose
                    signup_url="https://api.example.com/signup",  # Where to get key
                    is_required=True,  # False for optional enhancements
                ),
                # Add more API key requirements as needed
            ],
            # Rate limiting (requests per minute)
            rate_limit=60,  # Be respectful to API providers
            # Request timeout (seconds)
            timeout=30,  # Based on API response times
            # Plugin author (defaults to "KISS Team")
            author="Your Name",
            # Dependencies on other plugins (optional)
            dependencies=["other_plugin_name"],  # Remove if no dependencies
        )

    async def scan_async(
        self,
        target: str,
        scan_type: str,
        progress_callback: Callable[[float], None],
    ) -> List[Dict[str, Any]]:
        """Execute async scan and return results.

        This is the main plugin method that performs the actual OSINT work.
        Use async/await for all I/O operations (HTTP requests, file I/O, etc.).

        Args:
            target: The target to scan (email, IP, phone, etc.)
            scan_type: The type of scan being performed
            progress_callback: Function to report progress (0.0-1.0)

        Returns:
            List of result dictionaries with standardized format

        Result Dictionary Format:
            {
                "label": "Result Label",           # Human-readable label
                "value": "Result Value",           # The actual result
                "source": "Your Plugin Name",      # Data source (auto-filled)
                "threat_level": "LOW|MEDIUM|HIGH|CRITICAL",  # Optional
                "confidence": 0.95,               # Optional (0.0-1.0)
                "metadata": {                       # Optional additional data
                    "field1": "value1",
                    "field2": "value2",
                }
            }

        Progress Callback:
            Call progress_callback(progress) where progress is 0.0-1.0
            Example: progress_callback(0.5) for 50% complete
        """
        results: List[Dict[str, Any]] = []

        # === STEP 1: Initial Setup and Validation ===
        progress_callback(0.1)

        # Check if plugin is properly configured
        if not self.is_configured():
            missing_keys = self.get_missing_keys()
            results.append(
                self._create_result(
                    "Configuration Error",
                    f"Missing API keys: {', '.join(req.display_name for req in missing_keys)}",
                    threat_level="HIGH",
                    confidence=1.0,
                    metadata={"missing_keys": [req.key_name for req in missing_keys]},
                )
            )
            progress_callback(1.0)
            return results

        # Validate target format for supported scan types
        if scan_type == "EMAIL":
            if not self._validate_email(target):
                results.append(
                    self._create_result(
                        "Validation Error",
                        "Invalid email format",
                        threat_level="HIGH",
                    )
                )
                progress_callback(1.0)
                return results

        elif scan_type == "PHONE":
            if not self._validate_phone(target):
                results.append(
                    self._create_result(
                        "Validation Error",
                        "Invalid phone format",
                        threat_level="HIGH",
                    )
                )
                progress_callback(1.0)
                return results

        # === STEP 2: Prepare API Request ===
        progress_callback(0.3)

        # Prepare your API request here
        api_url = "https://api.example.com/endpoint"
        params = {
            "target": target,
            "type": scan_type.lower(),
            # Add other parameters as needed
        }

        headers = {
            "Authorization": f"Bearer {self.get_api_key('api_name')}",
            "Content-Type": "application/json",
        }

        # === STEP 3: Execute API Request ===
        progress_callback(0.5)

        try:
            # Make async HTTP request using the helper method
            response = await self._make_request(
                url=api_url,
                method="GET",
                params=params,
                headers=headers,
            )

            if response is None:
                results.append(
                    self._create_result(
                        "Network Error",
                        "Failed to connect to API service",
                        threat_level="MEDIUM",
                    )
                )
                progress_callback(1.0)
                return results

            # === STEP 4: Process Response ===
            progress_callback(0.7)

            if response.status == 200:
                try:
                    data = await response.json()

                    # Process the data according to your API's response format
                    results.extend(self._process_api_response(data, target))

                except Exception as e:
                    results.append(
                        self._create_result(
                            "Response Error",
                            f"Failed to parse API response: {str(e)}",
                            threat_level="MEDIUM",
                        )
                    )
            else:
                results.append(
                    self._create_result(
                        "API Error",
                        f"API returned status {response.status}",
                        threat_level="HIGH",
                        metadata={"status_code": response.status},
                    )
                )

        except Exception as e:
            results.append(
                self._create_result(
                    "Request Error",
                    f"Request failed: {str(e)}",
                    threat_level="HIGH",
                )
            )

        # === STEP 5: Final Processing ===
        progress_callback(0.9)

        # Add any final processing or additional results here

        progress_callback(1.0)
        return results

    # === Helper Methods ===

    def _validate_email(self, email: str) -> bool:
        """Validate email format."""
        import re

        pattern = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
        return bool(pattern.match(email))

    def _validate_phone(self, phone: str) -> bool:
        """Validate phone format."""
        import re

        pattern = re.compile(r"^\+?[\d\s\-\(\)]{10,}$")
        return bool(pattern.match(phone))

    async def _process_api_response(
        self, data: Dict[str, Any], target: str
    ) -> List[Dict[str, Any]]:
        """Process API response and return standardized results.

        Override this method to handle your specific API response format.

        Args:
            data: JSON response from API
            target: Original target being scanned

        Returns:
            List of result dictionaries
        """
        results = []

        # Example processing - adapt to your API's format
        if "results" in data:
            for item in data["results"]:
                # Basic result
                result = self._create_result(
                    label=item.get("label", "Unknown"),
                    value=item.get("value", ""),
                    threat_level=item.get("threat_level"),
                    confidence=item.get("confidence", 1.0),
                )

                # Add metadata if available
                if "metadata" in item:
                    result["metadata"] = item["metadata"]

                results.append(result)

        # If no results, add a "not found" result
        if not results:
            results.append(
                self._create_result(
                    label="Search Results",
                    value=f"No results found for {target}",
                    confidence=1.0,
                )
            )

        return results

    # === Additional Helper Methods (Optional) ===

    async def _make_custom_request(
        self, endpoint: str, data: Dict[str, Any]
    ) -> Optional[Any]:
        """Example of a custom request method for specific API needs."""

        # Custom headers for this specific endpoint
        headers = {
            "Authorization": f"Bearer {self.get_api_key('api_name')}",
            "User-Agent": "KISS/2.0 (OSINT Tool)",
            "Accept": "application/json",
        }

        try:
            response = await self._make_request(
                url=f"https://api.example.com/{endpoint}",
                method="POST",
                json_data=data,
                headers=headers,
            )

            if response and response.status == 200:
                return await response.json()

        except Exception as e:
            # Log error if you have logging
            pass

        return None

    def _get_additional_config(self, key: str, default: Any = None) -> Any:
        """Get additional configuration values."""
        # Example: getting custom config values
        if hasattr(self.config, "plugin_configs"):
            plugin_config = self.config.plugin_configs.get(self.metadata.name, {})
            return plugin_config.get(key, default)
        return default
