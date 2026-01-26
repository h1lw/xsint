"""Nominatim Plugin.

Geocodes physical addresses using OpenStreetMap's Nominatim service.
"""

from typing import Any, Callable, Dict, List

from ..base import BasePlugin, PluginMetadata


class NominatimPlugin(BasePlugin):
    """Nominatim geocoding plugin."""

    BASE_URL = "https://nominatim.openstreetmap.org"

    @classmethod
    def get_metadata(cls) -> PluginMetadata:
        return PluginMetadata(
            name="nominatim",
            display_name="Nominatim (OSM)",
            description="Geocode addresses via OpenStreetMap",
            version="1.0.0",
            category="Identity Lookup",
            supported_scan_types=["ADDRESS"],
            api_key_requirements=[],  # No API key required
            rate_limit=60,  # Nominatim asks for max 1 req/sec
            timeout=30,
        )

    def scan(
        self,
        target: str,
        scan_type: str,
        progress_callback: Callable[[float], None],
    ) -> List[Dict[str, Any]]:
        """Execute address geocoding."""
        results: List[Dict[str, Any]] = []
        progress_callback(0.2)

        url = f"{self.BASE_URL}/search"
        params = {
            "q": target,
            "format": "json",
            "limit": 1,
            "addressdetails": 1,
        }

        response = self._make_request(url, params=params)
        progress_callback(0.6)

        if response is None:
            results.append(
                self._create_result(
                    "Geocoding",
                    "Service unavailable",
                )
            )
            progress_callback(1.0)
            return results

        if response.status_code == 200:
            try:
                data = response.json()

                if data:
                    location = data[0]

                    # Formatted address
                    display_name = location.get("display_name", "")
                    if display_name:
                        results.append(
                            self._create_result(
                                "Formatted Address",
                                display_name,
                            )
                        )

                    # Coordinates
                    lat = location.get("lat", "")
                    lon = location.get("lon", "")
                    if lat and lon:
                        results.append(
                            self._create_result(
                                "Coordinates",
                                f"{lat}, {lon}",
                            )
                        )

                    # Address components
                    addr = location.get("address", {})

                    # Country
                    country = addr.get("country", "")
                    if country:
                        results.append(
                            self._create_result(
                                "Country",
                                country,
                            )
                        )

                    # State/Province
                    state = addr.get("state", addr.get("province", ""))
                    if state:
                        results.append(
                            self._create_result(
                                "State/Province",
                                state,
                            )
                        )

                    # City
                    city = addr.get("city", addr.get("town", addr.get("village", "")))
                    if city:
                        results.append(
                            self._create_result(
                                "City",
                                city,
                            )
                        )

                    # Postcode
                    postcode = addr.get("postcode", "")
                    if postcode:
                        results.append(
                            self._create_result(
                                "Postal Code",
                                postcode,
                            )
                        )

                    # Place type
                    place_type = location.get("type", "")
                    place_class = location.get("class", "")
                    if place_type or place_class:
                        results.append(
                            self._create_result(
                                "Place Type",
                                f"{place_class}/{place_type}".strip("/"),
                            )
                        )

                    # Bounding box
                    bbox = location.get("boundingbox", [])
                    if len(bbox) == 4:
                        results.append(
                            self._create_result(
                                "Bounding Box",
                                f"[{bbox[0]}, {bbox[2]}] to [{bbox[1]}, {bbox[3]}]",
                            )
                        )

                    # OSM info
                    osm_type = location.get("osm_type", "")
                    osm_id = location.get("osm_id", "")
                    if osm_type and osm_id:
                        results.append(
                            self._create_result(
                                "OSM Reference",
                                f"{osm_type}/{osm_id}",
                            )
                        )

                else:
                    results.append(
                        self._create_result(
                            "Geocoding",
                            "Address not found",
                        )
                    )

            except (ValueError, KeyError):
                results.append(
                    self._create_result(
                        "Geocoding",
                        "Failed to parse response",
                    )
                )

        progress_callback(1.0)
        return results
