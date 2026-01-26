"""Have I Been Pwned Plugin.

Checks for data breaches and pastes via the HIBP API v3.
"""

from typing import Any, Callable, Dict, List

from ..base import APIKeyRequirement, BasePlugin, PluginMetadata


class HIBPPlugin(BasePlugin):
    """Have I Been Pwned breach detection plugin."""

    @classmethod
    def get_metadata(cls) -> PluginMetadata:
        return PluginMetadata(
            name="hibp",
            display_name="Have I Been Pwned",
            description="Check for data breaches and pastes via HIBP API",
            version="1.0.0",
            category="Breach Detection",
            supported_scan_types=["EMAIL", "DOMAIN"],
            api_key_requirements=[
                APIKeyRequirement(
                    key_name="hibp",
                    env_var="KISS_HIBP_API_KEY",
                    display_name="HIBP API Key",
                    description="Required for breach checking via HIBP API v3",
                    signup_url="https://haveibeenpwned.com/API/Key",
                    is_required=True,
                )
            ],
            rate_limit=120,
            timeout=30,
        )

    def scan(
        self,
        target: str,
        scan_type: str,
        progress_callback: Callable[[float], None],
    ) -> List[Dict[str, Any]]:
        """Execute HIBP breach check."""
        results: List[Dict[str, Any]] = []

        if not self.is_configured():
            results.append(
                self._create_result(
                    "HIBP Breaches",
                    "API key required - set KISS_HIBP_API_KEY",
                    threat_level="LOW",
                )
            )
            progress_callback(1.0)
            return results

        api_key = self.get_api_key("hibp")
        progress_callback(0.2)

        # Check breaches
        breach_results = self._check_breaches(target, api_key)
        results.extend(breach_results)
        progress_callback(0.6)

        # Check pastes (email only)
        if scan_type.upper() == "EMAIL":
            paste_results = self._check_pastes(target, api_key)
            results.extend(paste_results)

        progress_callback(1.0)
        return results

    def _check_breaches(self, target: str, api_key: str) -> List[Dict[str, Any]]:
        """Check for data breaches."""
        results: List[Dict[str, Any]] = []

        url = f"https://haveibeenpwned.com/api/v3/breachedaccount/{target}"
        headers = {
            "hibp-api-key": api_key,
            "User-Agent": "KISS/2.0 (OSINT Tool)",
        }

        response = self._make_request(url, headers=headers)

        if response is None:
            return results

        if response.status_code == 200:
            try:
                breaches = response.json()
                breach_names = [b.get("Name", "Unknown") for b in breaches[:5]]
                total = len(breaches)

                results.append(
                    self._create_result(
                        "Data Breaches",
                        f"FOUND IN {total} BREACHES: {', '.join(breach_names)}"
                        + ("..." if total > 5 else ""),
                        threat_level="HIGH",
                    )
                )

                # Add breach details
                for breach in breaches[:3]:
                    name = breach.get("Name", "Unknown")
                    date = breach.get("BreachDate", "Unknown")
                    data_classes = breach.get("DataClasses", [])
                    exposed = ", ".join(data_classes[:3])
                    results.append(
                        self._create_result(
                            f"Breach: {name}",
                            f"Date: {date} | Exposed: {exposed}",
                            threat_level="MEDIUM",
                        )
                    )

            except (ValueError, KeyError):
                pass

        elif response.status_code == 404:
            results.append(
                self._create_result(
                    "Data Breaches",
                    "No breaches found",
                )
            )
        elif response.status_code == 401:
            results.append(
                self._create_result(
                    "HIBP",
                    "Invalid API key",
                    threat_level="LOW",
                )
            )
        elif response.status_code == 429:
            results.append(
                self._create_result(
                    "HIBP",
                    "Rate limited - try again later",
                    threat_level="LOW",
                )
            )

        return results

    def _check_pastes(self, email: str, api_key: str) -> List[Dict[str, Any]]:
        """Check for pastes containing the email."""
        results: List[Dict[str, Any]] = []

        url = f"https://haveibeenpwned.com/api/v3/pasteaccount/{email}"
        headers = {
            "hibp-api-key": api_key,
            "User-Agent": "KISS/2.0 (OSINT Tool)",
        }

        response = self._make_request(url, headers=headers)

        if response is None:
            return results

        if response.status_code == 200:
            try:
                pastes = response.json()
                if pastes:
                    results.append(
                        self._create_result(
                            "Pastes",
                            f"Found in {len(pastes)} paste(s)",
                            threat_level="MEDIUM",
                        )
                    )
            except (ValueError, KeyError):
                pass
        elif response.status_code == 404:
            results.append(
                self._create_result(
                    "Pastes",
                    "No pastes found",
                )
            )

        return results
