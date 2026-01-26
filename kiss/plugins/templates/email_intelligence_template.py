"""
Email Intelligence Plugin Template

This template demonstrates how to create an async email intelligence plugin.
Follow this structure to build custom plugins for KISS.
"""

from typing import Any, Callable, Dict, List, Optional

from kiss.plugins.async_base import AsyncBasePlugin, PluginMetadata, APIKeyRequirement


class EmailIntelligencePlugin(AsyncBasePlugin):
    """
    Email Intelligence Plugin Template

    This plugin demonstrates email analysis capabilities including:
    - Domain analysis
    - Email format validation
    - Provider detection
    - Threat assessment

    Replace this with your actual plugin logic.
    """

    @classmethod
    def get_metadata(cls) -> PluginMetadata:
        """Return plugin metadata. Required for all plugins."""
        return PluginMetadata(
            name="email_intelligence",
            display_name="Email Intelligence",
            description="Advanced email analysis and threat detection",
            version="1.0.0",
            category="Email Intelligence",
            supported_scan_types=["EMAIL"],
            api_key_requirements=[
                APIKeyRequirement(
                    key_name="email_api",
                    env_var="KISS_EMAIL_API_KEY",
                    display_name="Email API Key",
                    description="Required for email intelligence lookup",
                    signup_url="https://api.example.com/signup",
                    is_required=True,
                )
            ],
            rate_limit=60,  # Requests per minute
            timeout=30,  # Request timeout in seconds
            author="Your Name",
            dependencies=[],  # Other plugins this depends on
        )

    async def scan_async(
        self,
        target: str,
        scan_type: str,
        progress_callback: Callable[[float], None],
    ) -> List[Dict[str, Any]]:
        """
        Execute async email intelligence scan.

        Args:
            target: Email address to analyze
            scan_type: Should be "EMAIL"
            progress_callback: Progress reporting function (0.0-1.0)

        Returns:
            List of result dictionaries with standardized format
        """
        results: List[Dict[str, Any]] = []
        progress_callback(0.1)

        # Validate input
        if scan_type != "EMAIL":
            return [
                self._create_result(
                    "Error",
                    "This plugin only supports EMAIL scan type",
                    threat_level="HIGH",
                )
            ]

        progress_callback(0.2)

        # Basic email analysis (example implementation)
        try:
            # Extract domain from email
            domain = target.split("@")[-1].lower()

            # Domain analysis
            results.append(self._create_result("Domain", domain, source="Email Parser"))

            progress_callback(0.4)

            # Check for common providers
            common_providers = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com"]
            if domain in common_providers:
                results.append(
                    self._create_result(
                        "Provider Type",
                        "Common Email Provider",
                        source="Provider Analysis",
                    )
                )

            progress_callback(0.6)

            # Example API call (replace with actual API)
            if self.is_configured():
                api_results = await self._query_api(target)
                results.extend(api_results)
            else:
                results.append(
                    self._create_result(
                        "API Analysis",
                        "API key not configured - limited analysis only",
                        threat_level="MEDIUM",
                    )
                )

            progress_callback(0.8)

            # Additional analysis
            results.append(
                self._create_result("Email Format", "Valid", source="Format Validation")
            )

            progress_callback(1.0)

        except Exception as e:
            results.append(
                self._create_result(
                    "Scan Error",
                    f"Email analysis failed: {str(e)}",
                    threat_level="HIGH",
                )
            )

        return results

    async def _query_api(self, email: str) -> List[Dict[str, Any]]:
        """
        Example API integration method.

        Replace with your actual API integration.
        This is just a demonstration of async HTTP requests.
        """
        results: List[Dict[str, Any]] = []

        try:
            # Get API key
            api_key = self.get_api_key("email_api")
            if not api_key:
                return results

            # Example API endpoint (replace with real endpoint)
            url = "https://api.example.com/email/check"
            params = {"email": email, "api_key": api_key}

            # Make async request
            response = await self._make_request(url, method="GET", params=params)

            if response and response.status == 200:
                data = await response.json()

                # Process API response
                if data.get("breached"):
                    results.append(
                        self._create_result(
                            "Breach Status",
                            f"Found in {data.get('breach_count', 0)} breaches",
                            threat_level="HIGH",
                            source="Email API",
                        )
                    )

                if data.get("disposable"):
                    results.append(
                        self._create_result(
                            "Email Type",
                            "Disposable/Temporary",
                            threat_level="MEDIUM",
                            source="Email API",
                        )
                    )

                if data.get("deliverable"):
                    results.append(
                        self._create_result(
                            "Deliverability", "Deliverable", source="Email API"
                        )
                    )

        except Exception as e:
            # API errors should not crash the plugin
            results.append(
                self._create_result(
                    "API Error",
                    f"API request failed: {str(e)}",
                    threat_level="MEDIUM",
                    source="Email API",
                )
            )

        return results

    # Optional: Override rate limiting for custom behavior
    async def _rate_limit(self):
        """Custom rate limiting if needed."""
        # Use default rate limiting or implement custom logic
        await super()._rate_limit()

    # Optional: Custom validation
    def _validate_email_format(self, email: str) -> bool:
        """Custom email validation if needed."""
        import re

        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(pattern, email))


# Plugin registration information
# This plugin will be automatically discovered by KISS if placed in:
# ~/.kiss/plugins/email_intelligence.py
# or in the kiss/plugins/ directory with proper __init__.py
