"""Platform Check Plugin.

Checks username availability across common platforms.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable, Dict, List, Tuple

from ..base import BasePlugin, PluginMetadata


class PlatformCheckPlugin(BasePlugin):
    """Username platform enumeration plugin."""

    # Platform configurations: (name, url_template, check_method)
    PLATFORMS = [
        ("GitHub", "https://github.com/{}", "head_200"),
        ("Twitter/X", "https://twitter.com/{}", "head_200"),
        ("Instagram", "https://instagram.com/{}", "head_200"),
        ("Reddit", "https://reddit.com/user/{}", "head_200"),
        ("LinkedIn", "https://linkedin.com/in/{}", "head_200"),
        ("TikTok", "https://tiktok.com/@{}", "head_200"),
        ("YouTube", "https://youtube.com/@{}", "head_200"),
        ("Pinterest", "https://pinterest.com/{}", "head_200"),
        ("Twitch", "https://twitch.tv/{}", "head_200"),
        ("Steam", "https://steamcommunity.com/id/{}", "head_200"),
        ("Medium", "https://medium.com/@{}", "head_200"),
        ("DevTo", "https://dev.to/{}", "head_200"),
        ("HackerNews", "https://news.ycombinator.com/user?id={}", "head_200"),
        ("Keybase", "https://keybase.io/{}", "head_200"),
    ]

    @classmethod
    def get_metadata(cls) -> PluginMetadata:
        return PluginMetadata(
            name="platform_check",
            display_name="Platform Check",
            description="Check username across social platforms",
            version="1.0.0",
            category="Username Enumeration",
            supported_scan_types=["USERNAME"],
            api_key_requirements=[],  # No API key required
            rate_limit=30,  # Be respectful to platforms
            timeout=10,
        )

    def scan(
        self,
        target: str,
        scan_type: str,
        progress_callback: Callable[[float], None],
    ) -> List[Dict[str, Any]]:
        """Execute platform checks."""
        results: List[Dict[str, Any]] = []
        progress_callback(0.1)

        # Clean username
        username = target.lstrip("@").strip()

        if not username:
            results.append(
                self._create_result(
                    "Username Check",
                    "Invalid username",
                    threat_level="LOW",
                )
            )
            progress_callback(1.0)
            return results

        # Check platforms in parallel
        found_platforms: List[str] = []
        not_found_platforms: List[str] = []
        checked = 0
        total = len(self.PLATFORMS)

        # Use thread pool for parallel checks
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(self._check_platform, username, platform): platform
                for platform in self.PLATFORMS
            }

            for future in as_completed(futures):
                platform = futures[future]
                try:
                    name, exists, url = future.result()
                    if exists:
                        found_platforms.append(name)
                    else:
                        not_found_platforms.append(name)
                except Exception:
                    pass

                checked += 1
                progress_callback(0.1 + (0.8 * checked / total))

        # Summary result
        if found_platforms:
            results.append(
                self._create_result(
                    "Found On",
                    ", ".join(found_platforms),
                )
            )

            # Add individual platform results with URLs
            for platform in self.PLATFORMS:
                name, url_template, _ = platform
                if name in found_platforms:
                    url = url_template.format(username)
                    results.append(
                        self._create_result(
                            f"Profile: {name}",
                            url,
                        )
                    )
        else:
            results.append(
                self._create_result(
                    "Platforms",
                    "Username not found on common platforms",
                )
            )

        # Stats
        results.append(
            self._create_result(
                "Stats",
                f"Found: {len(found_platforms)}/{total} platforms checked",
            )
        )

        progress_callback(1.0)
        return results

    def _check_platform(
        self, username: str, platform: Tuple[str, str, str]
    ) -> Tuple[str, bool, str]:
        """Check if username exists on a platform.

        Args:
            username: The username to check
            platform: Tuple of (name, url_template, check_method)

        Returns:
            Tuple of (platform_name, exists, url)
        """
        name, url_template, check_method = platform
        url = url_template.format(username)

        try:
            if check_method == "head_200":
                response = self._make_request(url, method="HEAD")
                if response is not None:
                    # Most platforms return 200 if user exists
                    exists = response.status_code == 200
                    return (name, exists, url)
        except Exception:
            pass

        return (name, False, url)
