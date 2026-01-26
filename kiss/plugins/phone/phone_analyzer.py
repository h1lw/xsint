"""Phone Analyzer Plugin.

Analyzes phone numbers using the phonenumbers library.
"""

from typing import Any, Callable, Dict, List

from ..base import BasePlugin, PluginMetadata


class PhoneAnalyzerPlugin(BasePlugin):
    """Phone number analysis plugin."""

    # Line type mapping
    LINE_TYPE_MAPPING = {
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
        10: "Emergency",
        11: "Voicemail",
        12: "Short Code",
        13: "Standard Rate",
    }

    @classmethod
    def get_metadata(cls) -> PluginMetadata:
        return PluginMetadata(
            name="phone_analyzer",
            display_name="Phone Analyzer",
            description="Analyze phone numbers using phonenumbers library",
            version="1.0.0",
            category="Phone Intelligence",
            supported_scan_types=["PHONE"],
            api_key_requirements=[],  # No API key - uses local library
            rate_limit=1000,  # Local processing, no real limit
            timeout=10,
        )

    def scan(
        self,
        target: str,
        scan_type: str,
        progress_callback: Callable[[float], None],
    ) -> List[Dict[str, Any]]:
        """Execute phone number analysis."""
        results: List[Dict[str, Any]] = []
        progress_callback(0.1)

        try:
            import phonenumbers
            from phonenumbers import carrier, geocoder, phonenumberutil, timezone
        except ImportError:
            results.append(
                self._create_result(
                    "Phone Analysis",
                    "phonenumbers library not installed",
                    threat_level="LOW",
                )
            )
            progress_callback(1.0)
            return results

        progress_callback(0.2)

        try:
            # Parse phone number
            parsed_number = phonenumbers.parse(target, None)

            # Validate
            if not phonenumbers.is_valid_number(parsed_number):
                results.append(
                    self._create_result(
                        "Validation",
                        "Invalid phone number format",
                        threat_level="HIGH",
                    )
                )
                progress_callback(1.0)
                return results

            results.append(
                self._create_result(
                    "Validation",
                    "Valid phone number",
                )
            )

            progress_callback(0.3)

            # Carrier information
            carrier_name = carrier.name_for_number(parsed_number, "en")
            if carrier_name:
                results.append(
                    self._create_result(
                        "Carrier",
                        carrier_name,
                    )
                )

            progress_callback(0.4)

            # Line type
            number_type = phonenumberutil.number_type(parsed_number)
            if number_type in self.LINE_TYPE_MAPPING:
                line_desc = self.LINE_TYPE_MAPPING[number_type]

                # Assign threat level based on line type
                threat_level = None
                if number_type == 6:  # VoIP
                    threat_level = "MEDIUM"
                elif number_type == 3:  # Toll-Free
                    threat_level = "MEDIUM"
                elif number_type == 4:  # Premium Rate
                    threat_level = "HIGH"

                results.append(
                    self._create_result(
                        "Line Type",
                        line_desc,
                        threat_level=threat_level,
                    )
                )

            progress_callback(0.5)

            # Geographic information
            region = geocoder.description_for_number(parsed_number, "en")
            if region:
                results.append(
                    self._create_result(
                        "Region/City",
                        region,
                    )
                )

            country = geocoder.country_name_for_number(parsed_number, "en")
            if country:
                results.append(
                    self._create_result(
                        "Country",
                        country,
                    )
                )

            progress_callback(0.6)

            # Timezone information
            timezones = timezone.time_zones_for_number(parsed_number)
            if timezones:
                tz_display = ", ".join(list(timezones)[:2])
                if len(timezones) > 2:
                    tz_display += f" (+{len(timezones) - 2} more)"
                results.append(
                    self._create_result(
                        "Timezone(s)",
                        tz_display,
                    )
                )

            progress_callback(0.7)

            # Format information
            try:
                intl_format = phonenumbers.format_number(
                    parsed_number, phonenumbers.PhoneNumberFormat.INTERNATIONAL
                )
                national_format = phonenumbers.format_number(
                    parsed_number, phonenumbers.PhoneNumberFormat.NATIONAL
                )
                e164_format = phonenumbers.format_number(
                    parsed_number, phonenumbers.PhoneNumberFormat.E164
                )

                results.append(
                    self._create_result(
                        "International Format",
                        intl_format,
                    )
                )
                results.append(
                    self._create_result(
                        "National Format",
                        national_format,
                    )
                )
                results.append(
                    self._create_result(
                        "E.164 Format",
                        e164_format,
                    )
                )
            except Exception:
                pass

            progress_callback(0.8)

            # Country code
            if hasattr(parsed_number, "country_code") and parsed_number.country_code:
                results.append(
                    self._create_result(
                        "Country Code",
                        f"+{parsed_number.country_code}",
                    )
                )

            # National number
            if hasattr(parsed_number, "national_number") and parsed_number.national_number:
                results.append(
                    self._create_result(
                        "National Number",
                        str(parsed_number.national_number),
                    )
                )

            progress_callback(0.9)

            # Additional checks
            is_possible = phonenumbers.is_possible_number(parsed_number)
            if not is_possible:
                results.append(
                    self._create_result(
                        "Warning",
                        "Number may not be dialable",
                        threat_level="LOW",
                    )
                )

        except Exception as e:
            results.append(
                self._create_result(
                    "Phone Analysis",
                    f"Analysis failed: {str(e)}",
                    threat_level="LOW",
                )
            )

        progress_callback(1.0)
        return results
