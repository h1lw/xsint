"""Async Plugin Base Classes.

Defines abstract base class and data structures for all KISS async plugins.
Provides backward compatibility with existing sync plugins.
"""

import os
import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

import aiohttp


@dataclass
class APIKeyRequirement:
    """Describes an API key requirement for a plugin."""

    key_name: str  # e.g., "hibp"
    env_var: str  # e.g., "KISS_HIBP_API_KEY"
    display_name: str  # e.g., "Have I Been Pwned API Key"
    description: str  # e.g., "Required for breach checking"
    signup_url: Optional[str] = None  # e.g., "https://haveibeenpwned.com/API/Key"
    is_required: bool = True  # False = optional enhancement


@dataclass
class PluginMetadata:
    """Plugin metadata for registry and UI display."""

    name: str  # Unique identifier
    display_name: str  # Human-readable name
    description: str  # Brief description
    version: str  # Semantic version
    category: str  # "Breach Detection", "IP Intelligence", etc.
    supported_scan_types: List[str]  # ["EMAIL", "IP", "PHONE", etc.]
    api_key_requirements: List[APIKeyRequirement] = field(default_factory=list)
    rate_limit: int = 60  # Requests per minute
    timeout: int = 30  # Request timeout in seconds
    author: str = "KISS Team"
    dependencies: List[str] = field(default_factory=list)  # Other plugin names


class AsyncBasePlugin(ABC):
    """Abstract base class for all KISS async plugins/scanners.

    To create a custom async plugin:
    1. Subclass AsyncBasePlugin
    2. Implement get_metadata() returning PluginMetadata
    3. Implement scan_async() returning list of result dicts
    4. Implement optional rate limiting if needed
    5. Place file in ~/.kiss/plugins/ for auto-discovery

    Async Benefits:
    - Non-blocking I/O for HTTP requests
    - Better resource utilization
    - Higher concurrency with hundreds of modules
    - Faster overall scan times
    """

    def __init__(
        self,
        config: Any,
        session: Optional[aiohttp.ClientSession] = None,
        semaphore: Optional[asyncio.Semaphore] = None,
    ):
        """Initialize plugin with config and optional shared session.

        Args:
            config: KISSConfig instance for API keys and settings
            session: Optional aiohttp.ClientSession for connection pooling
            semaphore: Optional semaphore for rate limiting
        """
        self.config = config
        self.session = session or aiohttp.ClientSession()
        self.semaphore = semaphore
        self.metadata = self.get_metadata()
        self._last_request_time = 0.0
        self._rate_limit_lock = asyncio.Lock()

        # Set default headers
        if not self.session.headers:
            self.session.headers.update(
                {
                    "User-Agent": "KISS/2.0 (OSINT Tool)",
                    "Accept": "application/json",
                }
            )

    @classmethod
    @abstractmethod
    def get_metadata(cls) -> PluginMetadata:
        """Return plugin metadata. Must be implemented by all plugins.

        Returns:
            PluginMetadata instance describing plugin
        """
        pass

    @abstractmethod
    async def scan_async(
        self,
        target: str,
        scan_type: str,
        progress_callback: Callable[[float], None],
    ) -> List[Dict[str, Any]]:
        """Execute async scan and return results.

        Args:
            target: The target to scan (email, IP, phone, etc.)
            scan_type: The type of scan being performed
            progress_callback: Function to report progress (0.0-1.0)

        Returns:
            List of result dicts with keys: label, value, source,
            and optionally: threat_level, confidence, metadata
        """
        pass

    def scan(
        self,
        target: str,
        scan_type: str,
        progress_callback: Callable[[float], None],
    ) -> List[Dict[str, Any]]:
        """Synchronous wrapper for backward compatibility.

        Args:
            target: The target to scan
            scan_type: The type of scan being performed
            progress_callback: Function to report progress (0.0-1.0)

        Returns:
            List of result dicts
        """
        # Run async scan in event loop
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(
            self.scan_async(target, scan_type, progress_callback)
        )

    async def _rate_limit(self):
        """Apply rate limiting between requests using async primitives."""
        if self.metadata.rate_limit <= 0:
            return

        async with self._rate_limit_lock:
            min_interval = 60.0 / self.metadata.rate_limit
            elapsed = time.time() - self._last_request_time

            if elapsed < min_interval:
                await asyncio.sleep(min_interval - elapsed)

            self._last_request_time = time.time()

    async def _make_request(
        self,
        url: str,
        method: str = "GET",
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
        data: Optional[Dict] = None,
    ) -> Optional[aiohttp.ClientResponse]:
        """Make a rate-limited async HTTP request.

        Args:
            url: Request URL
            method: HTTP method (GET, POST, etc.)
            params: Query parameters
            headers: Additional headers
            json_data: JSON body for POST requests
            data: Form data for POST requests

        Returns:
            Response object or None on error
        """
        # Apply rate limiting if configured
        if self.semaphore:
            async with self.semaphore:
                return await self._make_request_internal(
                    url, method, params, headers, json_data, data
                )
        else:
            return await self._make_request_internal(
                url, method, params, headers, json_data, data
            )

    async def _make_request_internal(
        self,
        url: str,
        method: str,
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
        data: Optional[Dict] = None,
    ) -> Optional[aiohttp.ClientResponse]:
        """Internal request implementation with rate limiting."""
        await self._rate_limit()

        try:
            request_headers = dict(self.session.headers)
            if headers:
                request_headers.update(headers)

            timeout = aiohttp.ClientTimeout(total=self.metadata.timeout)

            method = method.upper()
            if method == "GET":
                async with self.session.get(
                    url,
                    params=params,
                    headers=request_headers,
                    timeout=timeout,
                ) as response:
                    return response
            elif method == "POST":
                async with self.session.post(
                    url,
                    params=params,
                    json=json_data,
                    data=data,
                    headers=request_headers,
                    timeout=timeout,
                ) as response:
                    return response
            elif method == "HEAD":
                async with self.session.head(
                    url,
                    params=params,
                    headers=request_headers,
                    timeout=timeout,
                    allow_redirects=True,
                ) as response:
                    return response
            else:
                return None

        except (aiohttp.ClientError, asyncio.TimeoutError):
            return None

    def is_configured(self) -> bool:
        """Check if plugin has all required API keys configured.

        Returns:
            True if all required API keys are present
        """
        for req in self.metadata.api_key_requirements:
            if req.is_required:
                key = self.get_api_key(req.key_name)
                if not key:
                    return False
        return True

    def get_missing_keys(self) -> List[APIKeyRequirement]:
        """Return list of missing required API keys.

        Returns:
            List of APIKeyRequirement for missing keys
        """
        missing = []
        for req in self.metadata.api_key_requirements:
            if req.is_required:
                key = self.get_api_key(req.key_name)
                if not key:
                    missing.append(req)
        return missing

    def get_api_key(self, key_name: str) -> Optional[str]:
        """Get an API key from config or environment.

        Args:
            key_name: The key name (e.g., "hibp")

        Returns:
            The API key value or None
        """
        # Try config first
        if hasattr(self.config, "get_api_key"):
            key = self.config.get_api_key(key_name.lower())
            if key:
                return key

        # Try environment variable
        for req in self.metadata.api_key_requirements:
            if req.key_name.lower() == key_name.lower():
                env_key = os.environ.get(req.env_var)
                if env_key:
                    return env_key

        return None

    def supports_scan_type(self, scan_type: str) -> bool:
        """Check if plugin supports given scan type.

        Args:
            scan_type: The scan type to check

        Returns:
            True if supported
        """
        return scan_type.upper() in [
            s.upper() for s in self.metadata.supported_scan_types
        ]

    def is_enabled(self) -> bool:
        """Check if plugin is enabled in config.

        Returns:
            True if enabled (default True if not in config)
        """
        if hasattr(self.config, "is_service_enabled"):
            return self.config.is_service_enabled(self.metadata.name)
        return True

    def _create_result(
        self,
        label: str,
        value: str,
        source: Optional[str] = None,
        threat_level: Optional[str] = None,
        confidence: float = 1.0,
        metadata: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Create a standardized result dict.

        Args:
            label: Result label/key
            value: Result value
            source: Data source name (defaults to plugin name)
            threat_level: Optional threat level (LOW, MEDIUM, HIGH, CRITICAL)
            confidence: Confidence score (0.0-1.0)
            metadata: Optional additional metadata

        Returns:
            Standardized result dict
        """
        result = {
            "label": label,
            "value": value,
            "source": source or self.metadata.display_name,
        }

        if threat_level:
            result["threat_level"] = threat_level

        if confidence != 1.0:
            result["confidence"] = confidence

        if metadata:
            result["metadata"] = metadata

        return result

    async def close(self):
        """Clean up resources. Override if needed."""
        if hasattr(self.session, "close"):
            await self.session.close()

    def __del__(self):
        """Cleanup on deletion."""
        if hasattr(self, "session") and hasattr(self.session, "close"):
            # Try to close session gracefully
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(self.close())
            except RuntimeError:
                pass


# Backward compatibility import
from .base import BasePlugin  # noqa: F401
