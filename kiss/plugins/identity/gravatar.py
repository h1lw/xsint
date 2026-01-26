"""Gravatar Plugin.

Looks up profile information from Gravatar.
"""

import hashlib
from typing import Any, Callable, Dict, List

from ..base import BasePlugin, PluginMetadata


class GravatarPlugin(BasePlugin):
    """Gravatar profile lookup plugin."""

    BASE_URL = "https://en.gravatar.com"

    @classmethod
    def get_metadata(cls) -> PluginMetadata:
        return PluginMetadata(
            name="gravatar",
            display_name="Gravatar",
            description="Email profile lookup via Gravatar",
            version="1.0.0",
            category="Identity Lookup",
            supported_scan_types=["EMAIL"],
            api_key_requirements=[],  # No API key required
            rate_limit=60,
            timeout=15,
        )

    def scan(
        self,
        target: str,
        scan_type: str,
        progress_callback: Callable[[float], None],
    ) -> List[Dict[str, Any]]:
        """Execute Gravatar lookup."""
        results: List[Dict[str, Any]] = []
        progress_callback(0.2)

        # Create email hash
        email_hash = hashlib.md5(target.lower().strip().encode()).hexdigest()

        url = f"{self.BASE_URL}/{email_hash}.json"
        response = self._make_request(url)
        progress_callback(0.6)

        if response is None:
            progress_callback(1.0)
            return results

        if response.status_code == 200:
            try:
                data = response.json()
                entry = data.get("entry", [{}])[0]

                # Display name
                display_name = entry.get("displayName", "")
                if display_name:
                    results.append(
                        self._create_result(
                            "Gravatar Name",
                            display_name,
                        )
                    )

                # About/bio
                about = entry.get("aboutMe", "")
                if about:
                    # Truncate long bios
                    about_text = about[:100] + "..." if len(about) > 100 else about
                    results.append(
                        self._create_result(
                            "About",
                            about_text,
                        )
                    )

                # Location
                location = entry.get("currentLocation", "")
                if location:
                    results.append(
                        self._create_result(
                            "Location",
                            location,
                        )
                    )

                # Profile URL
                profile_url = entry.get("profileUrl", "")
                if profile_url:
                    results.append(
                        self._create_result(
                            "Profile URL",
                            profile_url,
                        )
                    )

                # Linked accounts
                accounts = entry.get("accounts", [])
                if accounts:
                    account_names = [
                        a.get("shortname", a.get("domain", "unknown"))
                        for a in accounts[:5]
                    ]
                    results.append(
                        self._create_result(
                            "Linked Accounts",
                            ", ".join(account_names),
                        )
                    )

                    # Add individual account details
                    for account in accounts[:3]:
                        shortname = account.get("shortname", "")
                        username = account.get("username", "")
                        url = account.get("url", "")

                        if shortname and (username or url):
                            value = username if username else url
                            results.append(
                                self._create_result(
                                    f"Account: {shortname.title()}",
                                    value,
                                )
                            )

                # Photos
                photos = entry.get("photos", [])
                if photos:
                    results.append(
                        self._create_result(
                            "Profile Photos",
                            f"{len(photos)} photo(s) found",
                        )
                    )

                # URLs/websites
                urls = entry.get("urls", [])
                if urls:
                    for url_entry in urls[:2]:
                        title = url_entry.get("title", "Website")
                        url_value = url_entry.get("value", "")
                        if url_value:
                            results.append(
                                self._create_result(
                                    f"Website: {title}",
                                    url_value,
                                )
                            )

            except (ValueError, KeyError):
                pass

        elif response.status_code == 404:
            results.append(
                self._create_result(
                    "Gravatar",
                    "No profile found",
                )
            )

        progress_callback(1.0)
        return results
