"""Email account enumeration across consumer services.

Rewritten from kaifcodec/user-scanner (MIT) — fans out to every checker in
parallel and yields one finding per registered hit.
"""
import asyncio
import json
import time

import httpx

from xsint.config import get_config

INFO = {
    "free": ["email"],
    "returns": ["registered accounts"],
    "themes": {"EmailEnum": {"color": "magenta", "icon": "📧"}},
}

PARENT = "EmailEnum"
TIMEOUT = 7.0


async def _check_mixcloud(client, email):
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 Chrome/145.0.0.0 Mobile Safari/537.36",
        "Accept": "application/json",
        "x-requested-with": "XMLHttpRequest",
        "x-mixcloud-platform": "www",
        "origin": "https://www.mixcloud.com",
        "referer": "https://www.mixcloud.com/",
    }
    payload = {"email": email, "username": "you_ar3_al0n3_fight", "password": "", "ch": "y"}
    r = await client.post(
        "https://app.mixcloud.com/authentication/email-register/",
        data=payload, headers=headers,
    )
    if r.status_code != 200:
        return None
    errors = r.json().get("data", {}).get("$errors", {}).get("email", [])
    return any("already in use" in e for e in errors)


async def _check_spotify(client, email):
    payload = {
        "fields": [{"field": "FIELD_EMAIL", "value": email}],
        "client_info": {
            "api_key": "a1e486e2729f46d6bb368d6b2bcda326",
            "app_version": "v2",
            "capabilities": [1],
            "installation_id": "3740cfb5-c76f-4ae9-9a94-f0989d7ae5a4",
            "platform": "www",
            "client_id": "",
        },
        "tracking": {
            "creation_flow": "",
            "creation_point": "https://www.spotify.com/us/signup",
            "referrer": "", "origin_vertical": "", "origin_surface": "",
        },
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/144.0.0.0 Safari/537.36",
        "Content-Type": "application/json",
        "origin": "https://www.spotify.com",
        "referer": "https://www.spotify.com/",
    }
    r = await client.post(
        "https://spclient.wg.spotify.com/signup/public/v2/account/validate",
        content=json.dumps(payload), headers=headers,
    )
    data = r.json()
    if "error" in data and "already_exists" in data["error"]:
        return True
    if "success" in data:
        return False
    return None


async def _check_appletv(client, email):
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/144.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "X-Apple-Domain-Id": "2",
        "X-Apple-Locale": "en_us",
        "X-Apple-Auth-Context": "tv",
        "X-Requested-With": "XMLHttpRequest",
        "Origin": "https://idmsa.apple.com",
        "Referer": "https://idmsa.apple.com/",
    }
    r = await client.post(
        "https://idmsa.apple.com/appleauth/auth/federate",
        params={"isRememberMeEnabled": "false"},
        json={"accountName": email, "rememberMe": False},
        headers=headers,
    )
    if r.status_code != 200:
        return None
    return "primaryAuthOptions" in r.json()


async def _check_pinterest(client, email):
    data_str = json.dumps(
        {"options": {"url": "/v3/register/exists/", "data": {"email": email}}, "context": {}},
        separators=(",", ":"),
    )
    params = {
        "source_url": "/signup/step1/",
        "data": data_str,
        "_": str(int(time.time() * 1000)),
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 Chrome/144.0.0.0 Mobile Safari/537.36",
        "Accept": "application/json",
        "x-pinterest-pws-handler": "www/signup/[step].js",
        "x-app-version": "2503cde",
        "x-requested-with": "XMLHttpRequest",
        "x-pinterest-source-url": "/signup/step1/",
        "x-pinterest-appstate": "active",
        "origin": "https://www.pinterest.com",
        "referer": "https://www.pinterest.com/",
    }
    r = await client.get(
        "https://www.pinterest.com/resource/ApiResource/get/",
        params=params, headers=headers,
    )
    if r.status_code != 200:
        return None
    exists = r.json().get("resource_response", {}).get("data")
    return exists if isinstance(exists, bool) else None


SERVICES = [
    ("Mixcloud",  "https://mixcloud.com",  _check_mixcloud),
    ("Spotify",   "https://spotify.com",   _check_spotify),
    ("Apple TV",  "https://tv.apple.com",  _check_appletv),
    ("Pinterest", "https://pinterest.com", _check_pinterest),
]


async def _safe(name, url, fn, client, email):
    try:
        return name, url, await fn(client, email)
    except Exception:
        return name, url, None


async def run(session, target):
    if "@" not in target:
        return 1, []

    proxy = get_config().get("proxy")
    proxies = {"http://": proxy, "https://": proxy} if proxy else None

    async with httpx.AsyncClient(timeout=TIMEOUT, proxies=proxies, follow_redirects=True, verify=False) as client:
        results = await asyncio.gather(
            *(_safe(name, url, fn, client, target) for name, url, fn in SERVICES)
        )

    findings = [
        {"label": name, "value": url, "source": PARENT, "group": "Registered"}
        for name, url, hit in results if hit is True
    ]
    return 0, findings
