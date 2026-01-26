"""IPInfo Plugin.

Provides IP geolocation and network intelligence.
"""

from typing import Any, Callable, Dict, List

from ..base import APIKeyRequirement, BasePlugin, PluginMetadata


class IPInfoPlugin(BasePlugin):
    """IPInfo geolocation plugin."""

    BASE_URL = "https://ipinfo.io"

    @classmethod
    def get_metadata(cls) -> PluginMetadata:
        return PluginMetadata(
            name="ipinfo",
            display_name="IPInfo",
            description="IP geolocation and network intelligence",
            version="1.0.0",
            category="IP Intelligence",
            supported_scan_types=["IP"],
            api_key_requirements=[
                APIKeyRequirement(
                    key_name="ipinfo",
                    env_var="KISS_IPINFO_API_KEY",
                    display_name="IPInfo API Key",
                    description="Optional - increases rate limits",
                    signup_url="https://ipinfo.io/signup",
                    is_required=False,  # Works without key, just rate limited
                )
            ],
            rate_limit=1000,
            timeout=30,
        )

    def scan(
        self,
        target: str,
        scan_type: str,
        progress_callback: Callable[[float], None],
    ) -> List[Dict[str, Any]]:
        """Execute IP lookup."""
        results: List[Dict[str, Any]] = []
        progress_callback(0.2)

        url = f"{self.BASE_URL}/{target}/json"

        # Add auth header if API key available
        headers = {}
        api_key = self.get_api_key("ipinfo")
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        response = self._make_request(url, headers=headers)
        progress_callback(0.6)

        if response is None:
            results.append(
                self._create_result(
                    "IPInfo",
                    "Lookup failed - service unavailable",
                )
            )
            progress_callback(1.0)
            return results

        if response.status_code == 200:
            try:
                data = response.json()

                # Location info
                city = data.get("city", "")
                region = data.get("region", "")
                country = data.get("country", "")

                if city or region or country:
                    location_parts = [p for p in [city, region, country] if p]
                    results.append(
                        self._create_result(
                            "Location",
                            ", ".join(location_parts),
                        )
                    )

                # Organization/ISP
                org = data.get("org", "")
                if org:
                    results.append(
                        self._create_result(
                            "Organization",
                            org,
                        )
                    )

                # Hostname
                hostname = data.get("hostname", "")
                if hostname:
                    results.append(
                        self._create_result(
                            "Hostname",
                            hostname,
                        )
                    )

                # Coordinates
                loc = data.get("loc", "")
                if loc:
                    results.append(
                        self._create_result(
                            "Coordinates",
                            loc,
                        )
                    )

                # Timezone
                timezone = data.get("timezone", "")
                if timezone:
                    results.append(
                        self._create_result(
                            "Timezone",
                            timezone,
                        )
                    )

                # Postal code
                postal = data.get("postal", "")
                if postal:
                    results.append(
                        self._create_result(
                            "Postal Code",
                            postal,
                        )
                    )

                # Check for privacy flags (VPN, Proxy, etc.)
                privacy = data.get("privacy", {})
                if privacy:
                    if privacy.get("vpn"):
                        results.append(
                            self._create_result(
                                "VPN Detected",
                                "This IP is associated with a VPN service",
                                threat_level="MEDIUM",
                            )
                        )
                    if privacy.get("proxy"):
                        results.append(
                            self._create_result(
                                "Proxy Detected",
                                "This IP is associated with a proxy service",
                                threat_level="MEDIUM",
                            )
                        )
                    if privacy.get("tor"):
                        results.append(
                            self._create_result(
                                "Tor Exit Node",
                                "This IP is a Tor exit node",
                                threat_level="MEDIUM",
                            )
                        )
                    if privacy.get("hosting"):
                        results.append(
                            self._create_result(
                                "Hosting Provider",
                                "This IP belongs to a hosting provider",
                            )
                        )

            except (ValueError, KeyError):
                results.append(
                    self._create_result(
                        "IPInfo",
                        "Failed to parse response",
                    )
                )
        elif response.status_code == 429:
            results.append(
                self._create_result(
                    "IPInfo",
                    "Rate limited - add API key for higher limits",
                    threat_level="LOW",
                )
            )

        progress_callback(1.0)
        return results
