"""Check GitHub for a newer xsint release.

Synchronous, short-timeout, cache-backed. Stays out of the way:
- Off when XSINT_NO_VERSION_CHECK is set, --no-version-check is passed,
  or stdout isn't a TTY (so piped output stays clean).
- Cached for 24h in ~/.config/xsint/version_cache.json so we don't hit
  GitHub on every run.
- 1.5s timeout. If the network's down or GitHub is slow, the check
  silently degrades to whatever's in cache (or nothing).
"""
import json
import os
import re
import time
import urllib.request
from pathlib import Path
from typing import Optional, Tuple

from . import __version__

VERSION_URL = "https://raw.githubusercontent.com/h1lw/xsint/main/xsint/__init__.py"
CACHE_PATH = Path.home() / ".config" / "xsint" / "version_cache.json"
CACHE_TTL = 24 * 3600  # seconds
NETWORK_TIMEOUT = 1.5  # seconds


def _parse_version(text: str) -> Optional[str]:
    m = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', text)
    return m.group(1) if m else None


def _version_tuple(v: str) -> Tuple[int, ...]:
    out = []
    for p in v.split("."):
        try:
            out.append(int(p))
        except ValueError:
            # Strip any pre-release suffix and treat as 0.
            digits = re.match(r"\d+", p)
            out.append(int(digits.group(0)) if digits else 0)
    return tuple(out)


def _read_cache() -> Optional[dict]:
    try:
        with CACHE_PATH.open() as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def _write_cache(data: dict) -> None:
    try:
        CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with CACHE_PATH.open("w") as f:
            json.dump(data, f)
    except OSError:
        pass


def _fetch_latest() -> Optional[str]:
    try:
        req = urllib.request.Request(VERSION_URL, headers={"User-Agent": f"xsint/{__version__}"})
        with urllib.request.urlopen(req, timeout=NETWORK_TIMEOUT) as r:
            text = r.read().decode("utf-8", errors="replace")
        return _parse_version(text)
    except Exception:
        return None


def latest_version() -> Optional[str]:
    """Return the latest version published on main, or None."""
    cache = _read_cache()
    now = time.time()
    if cache and now - cache.get("ts", 0) < CACHE_TTL:
        return cache.get("version")

    fetched = _fetch_latest()
    if fetched:
        _write_cache({"ts": now, "version": fetched})
        return fetched

    # Stale cache is better than nothing.
    return cache.get("version") if cache else None


def check_for_update() -> Optional[Tuple[str, str]]:
    """Return (current, latest) if a newer version exists. Else None."""
    if os.environ.get("XSINT_NO_VERSION_CHECK"):
        return None
    latest = latest_version()
    if not latest:
        return None
    try:
        if _version_tuple(latest) > _version_tuple(__version__):
            return (__version__, latest)
    except Exception:
        return None
    return None
