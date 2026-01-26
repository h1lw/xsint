"""
Phone Intelligence Plugin Template

This template demonstrates how to create a phone intelligence plugin.
"""

from typing import Any, Callable, Dict, List, Optional

from kiss.plugins.async_base import AsyncBasePlugin, PluginMetadata, APIKeyRequirement


class PhoneIntelligencePlugin(AsyncBasePlugin):
    """
    Phone Intelligence Plugin Template

    This plugin demonstrates phone number analysis capabilities:
    - International format validation
    - Carrier detection
    - Geographic lookup
    - Line type analysis
    - Threat assessment

    Replace with your actual plugin logic.
    """

    @classmethod
    def get_metadata(cls) -> PluginMetadata:
        return PluginMetadata(
            name="phone_intelligence",
            display_name="Phone Intelligence",
            description="Advanced phone number analysis and carrier detection",
            version="1.0.0",
            category="Phone Intelligence",
            supported_scan_types=["PHONE"],
            api_key_requirements=[
                APIKeyRequirement(
                    key_name="phone_api",
                    env_var="KISS_PHONE_API_KEY",
                    display_name="Phone API Key",
                    description="Required for carrier and location lookup",
                    signup_url="https://api.example.com/signup",
                    is_required=True,
                )
            ],
            rate_limit=100,
            timeout=15,
            author="Your Name",
            dependencies=[],
        )

    async def scan_async(
        self,
        target: str,
        scan_type: str,
        progress_callback: Callable[[float], None],
    ) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        progress_callback(0.1)

        if scan_type != "PHONE":
            return [
                self._create_result(
                    "Error",
                    "This plugin only supports PHONE scan type",
                    threat_level="HIGH",
                )
            ]

        progress_callback(0.2)

        try:
            # Use phonenumbers for validation and parsing
            import phonenumbers

            parsed_number = phonenumbers.parse(target, None)

            if not phonenumbers.is_valid_number(parsed_number):
                results.append(
                    self._create_result(
                        "Validation", "Invalid phone number format", threat_level="HIGH"
                    )
                )
                progress_callback(1.0)
                return results

            results.append(
                self._create_result(
                    "Validation", "Valid phone number", source="Phone Validation"
                )
            )

            progress_callback(0.4)

            # Basic analysis (always available)
            country_code = getattr(parsed_number, "country_code", "Unknown")
            national_number = getattr(parsed_number, "national_number", 0)

            results.append(
                self._create_result(
                    "Country Code", f"+{country_code}", source="Phone Parser"
                )
            )

            results.append(
                self._create_result(
                    "National Number", str(national_number), source="Phone Parser"
                )
            )

            progress_callback(0.6)

            # API lookup if configured
            if self.is_configured():
                api_results = await self._lookup_phone_details(target)
                results.extend(api_results)
            else:
                results.append(
                    self._create_result(
                        "Enhanced Analysis",
                        "API key not configured - basic analysis only",
                        threat_level="MEDIUM",
                    )
                )

            progress_callback(0.8)

            # Line type analysis
            line_type = await self._analyze_line_type(target)
            results.append(
                self._create_result("Line Type", line_type, source="Line Analysis")
            )

            progress_callback(1.0)

        except Exception as e:
            results.append(
                self._create_result(
                    "Scan Error",
                    f"Phone analysis failed: {str(e)}",
                    threat_level="HIGH",
                )
            )

        return results

    async def _lookup_phone_details(self, phone: str) -> List[Dict[str, Any]]:
        """Lookup phone details via API."""
        results: List[Dict[str, Any]] = []

        try:
            api_key = self.get_api_key("phone_api")
            if not api_key:
                return results

            # Example API endpoint
            url = "https://api.example.com/phone/lookup"
            params = {"phone": phone, "api_key": api_key}

            response = await self._make_request(url, method="GET", params=params)

            if response and response.status == 200:
                data = await response.json()

                # Carrier information
                if data.get("carrier"):
                    results.append(
                        self._create_result(
                            "Carrier", data["carrier"]["name"], source="Phone API"
                        )
                    )

                # Location information
                if data.get("location"):
                    location = data["location"]
                    results.append(
                        self._create_result(
                            "Location",
                            f"{location.get('city', 'Unknown')}, {location.get('country', 'Unknown')}",
                            source="Phone API",
                        )
                    )

                # Timezone
                if data.get("timezone"):
                    results.append(
                        self._create_result(
                            "Timezone", data["timezone"], source="Phone API"
                        )
                    )

                # Threat assessment
                if data.get("is_voip"):
                    results.append(
                        self._create_result(
                            "Line Type",
                            "VoIP",
                            threat_level="MEDIUM",
                            source="Phone API",
                        )
                    )

                if data.get("is_disposable"):
                    results.append(
                        self._create_result(
                            "Phone Type",
                            "Disposable/Temporary",
                            threat_level="HIGH",
                            source="Phone API",
                        )
                    )

        except Exception as e:
            results.append(
                self._create_result(
                    "API Error", f"Phone lookup failed: {str(e)}", threat_level="MEDIUM"
                )
            )

        return results

    async def _analyze_line_type(self, phone: str) -> str:
        """Analyze line type based on number patterns."""
        # Simple pattern analysis (replace with actual logic)
        import phonenumbers
        from phonenumbers import phonenumberutil

        try:
            parsed = phonenumbers.parse(phone, None)
            number_type = phonenumberutil.number_type(parsed)

            type_mapping = {
                0: "Landline (Fixed Line)",
                1: "Mobile",
                2: "Landline or Mobile",
                3: "Toll-Free",
                4: "Premium Rate",
                5: "Shared Cost",
                6: "VoIP",
                7: "Personal Number",
                8: "Pager",
                9: "Unknown",
            }

            return type_mapping.get(number_type, "Unknown")
        except Exception:
            return "Unknown"
