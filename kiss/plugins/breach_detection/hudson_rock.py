"""Hudson Rock Plugin.

Checks for credentials in stealer malware logs.
"""

from typing import Any, Callable, Dict, List

from ..base import BasePlugin, PluginMetadata


class HudsonRockPlugin(BasePlugin):
    """Hudson Rock stealer malware check plugin."""

    BASE_URL = "https://cavalier.hudsonrock.com/api/json/v2/osint-tools"

    @classmethod
    def get_metadata(cls) -> PluginMetadata:
        return PluginMetadata(
            name="hudson_rock",
            display_name="Hudson Rock",
            description="Check for credentials in stealer malware logs",
            version="1.0.0",
            category="Breach Detection",
            supported_scan_types=["EMAIL", "IP", "PHONE", "DOMAIN"],
            api_key_requirements=[],  # No API key required
            rate_limit=30,
            timeout=30,
        )

    def scan(
        self,
        target: str,
        scan_type: str,
        progress_callback: Callable[[float], None],
    ) -> List[Dict[str, Any]]:
        """Execute Hudson Rock stealer check."""
        results: List[Dict[str, Any]] = []
        progress_callback(0.2)

        scan_type_upper = scan_type.upper()

        if scan_type_upper == "EMAIL":
            results.extend(self._check_email(target))
        elif scan_type_upper == "IP":
            results.extend(self._check_ip(target))
        elif scan_type_upper == "PHONE":
            results.extend(self._check_phone(target))
        elif scan_type_upper == "DOMAIN":
            results.extend(self._check_domain(target))

        progress_callback(1.0)
        return results

    def _check_email(self, email: str) -> List[Dict[str, Any]]:
        """Check email in stealer logs."""
        url = f"{self.BASE_URL}/search-by-email"
        params = {"email": email}

        return self._make_check(url, params, "email")

    def _check_ip(self, ip: str) -> List[Dict[str, Any]]:
        """Check IP in stealer logs."""
        url = f"{self.BASE_URL}/search-by-ip"
        params = {"ip": ip}

        return self._make_check(url, params, "IP")

    def _check_phone(self, phone: str) -> List[Dict[str, Any]]:
        """Check phone in stealer logs."""
        # Clean phone number
        clean_phone = "".join(c for c in phone if c.isdigit() or c == "+")

        url = f"{self.BASE_URL}/search-by-phone"
        params = {"phone": clean_phone}

        return self._make_check(url, params, "phone")

    def _check_domain(self, domain: str) -> List[Dict[str, Any]]:
        """Check domain in stealer logs."""
        url = f"{self.BASE_URL}/search-by-domain"
        params = {"domain": domain}

        return self._make_check(url, params, "domain")

    def _make_check(
        self, url: str, params: Dict[str, str], check_type: str
    ) -> List[Dict[str, Any]]:
        """Make a stealer log check request."""
        results: List[Dict[str, Any]] = []

        response = self._make_request(url, params=params)

        if response is None:
            results.append(
                self._create_result(
                    "Stealer Malware",
                    "Check failed - service unavailable",
                )
            )
            return results

        if response.status_code == 200:
            try:
                data = response.json()

                # Check if data was found
                if data.get("stealers") or data.get("total_results", 0) > 0:
                    count = data.get("total_results", len(data.get("stealers", [])))
                    results.append(
                        self._create_result(
                            "Stealer Malware",
                            f"COMPROMISED - Found in {count} stealer log(s)",
                            threat_level="CRITICAL",
                        )
                    )

                    # Add stealer details if available
                    stealers = data.get("stealers", [])
                    for stealer in stealers[:3]:
                        stealer_type = stealer.get("type", "Unknown")
                        date = stealer.get("date_compromised", "Unknown")
                        results.append(
                            self._create_result(
                                f"Stealer: {stealer_type}",
                                f"Compromised: {date}",
                                threat_level="HIGH",
                            )
                        )
                else:
                    results.append(
                        self._create_result(
                            "Stealer Malware",
                            "Not found in stealer logs",
                        )
                    )

            except (ValueError, KeyError):
                results.append(
                    self._create_result(
                        "Stealer Malware",
                        "Not found in stealer logs",
                    )
                )
        else:
            results.append(
                self._create_result(
                    "Stealer Malware",
                    "Not found in stealer logs",
                )
            )

        return results
