"""Phone account enumeration across consumer services.

Adapted from megadose/ignorant (AGPL/MIT-style) — runs the three known
phone-based "is this number registered" checks (Amazon, Instagram, Snapchat)
in parallel and reports one finding per registered hit.

Each check returns (hit: bool|None, url: str|None, extra: str|None).
"""
import asyncio
import hashlib
import hmac
import json
import urllib.parse

import httpx
import phonenumbers

INFO = {
    "free": ["phone"],
    "returns": ["registered accounts"],
    "themes": {"PhoneEnum": {"color": "magenta", "icon": "📱"}},
}

PARENT = "PhoneEnum"
PER_CHECK_TIMEOUT = 10.0
CONCURRENCY = 5

# E.164 country code -> ISO 3166-1 alpha-2 (subset Snapchat uses).
SNAP_CC_TO_ISO = {
    "1": "US", "7": "RU", "20": "EG", "27": "ZA", "30": "GR", "31": "NL",
    "32": "BE", "33": "FR", "34": "ES", "36": "HU", "39": "IT", "40": "RO",
    "41": "CH", "43": "AT", "44": "GB", "45": "DK", "46": "SE", "47": "NO",
    "48": "PL", "49": "DE", "51": "PE", "52": "MX", "53": "CU", "54": "AR",
    "55": "BR", "56": "CL", "57": "CO", "58": "VE", "60": "MY", "61": "AU",
    "62": "ID", "63": "PH", "64": "NZ", "65": "SG", "66": "TH", "81": "JP",
    "82": "KR", "84": "VN", "86": "CN", "90": "TR", "91": "IN", "92": "PK",
    "93": "AF", "94": "LK", "95": "MM", "98": "IR",
    "212": "MA", "213": "DZ", "216": "TN", "218": "LY", "220": "GM",
    "234": "NG", "254": "KE", "255": "TZ", "256": "UG", "260": "ZM",
    "263": "ZW", "351": "PT", "352": "LU", "353": "IE", "354": "IS",
    "355": "AL", "356": "MT", "357": "CY", "358": "FI", "359": "BG",
    "370": "LT", "371": "LV", "372": "EE", "373": "MD", "374": "AM",
    "375": "BY", "380": "UA", "385": "HR", "386": "SI", "387": "BA",
    "389": "MK", "420": "CZ", "421": "SK", "423": "LI", "880": "BD",
    "962": "JO", "964": "IQ", "965": "KW", "966": "SA", "967": "YE",
    "968": "OM", "971": "AE", "972": "IL", "973": "BH", "974": "QA",
    "977": "NP",
}


def _parse(target):
    """Return (country_code, national_number) as strings, or (None, None)."""
    try:
        parsed = phonenumbers.parse(target if target.startswith("+") else f"+{target}", None)
        return str(parsed.country_code), str(parsed.national_number)
    except Exception:
        return None, None


# --- Amazon (login probe) ---------------------------------------------------

async def _chk_amazon(cc, num):
    show_url = "https://amazon.com"
    headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"}
    try:
        async with httpx.AsyncClient(timeout=PER_CHECK_TIMEOUT, follow_redirects=True) as client:
            r = await client.get(
                "https://www.amazon.com/ap/signin?openid.pape.max_auth_age=0"
                "&openid.return_to=https%3A%2F%2Fwww.amazon.com%2F"
                "&openid.identity=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select"
                "&openid.assoc_handle=usflex&openid.mode=checkid_setup"
                "&openid.claimed_id=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select"
                "&openid.ns=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0",
                headers=headers,
            )
            # Lightweight HTML scrape (avoid bs4 dep)
            import re
            inputs = re.findall(r'<input[^>]+>', r.text)
            data = {}
            for tag in inputs:
                m_name = re.search(r'name="([^"]+)"', tag)
                m_val = re.search(r'value="([^"]*)"', tag)
                if m_name:
                    data[m_name.group(1)] = m_val.group(1) if m_val else ""
            data["email"] = f"{cc}{num}"
            r2 = await client.post("https://www.amazon.com/ap/signin/", data=data, headers=headers)
            if 'id="auth-password-missing-alert"' in r2.text:
                return (True, show_url, None)
            return (False, show_url, None)
    except Exception:
        return (None, None, None)


# --- Instagram (HMAC-signed users/lookup) -----------------------------------

_IG_SIG_KEY = "e6358aeede676184b9fe702b30f4fd35e71744605e39d2181a34cede076b3c33"
_IG_SIG_VER = "4"


def _ig_sign(data):
    digest = hmac.new(_IG_SIG_KEY.encode(), data.encode(), hashlib.sha256).hexdigest()
    return f"ig_sig_key_version={_IG_SIG_VER}&signed_body={digest}.{urllib.parse.quote_plus(data)}"


async def _chk_instagram(cc, num):
    show_url = "https://instagram.com"
    payload_json = json.dumps({
        "login_attempt_count": "0",
        "directly_sign_in": "true",
        "source": "default",
        "q": f"{cc}{num}",
        "ig_sig_key_version": _IG_SIG_VER,
    })
    body = _ig_sign(payload_json)
    headers = {
        "Accept-Language": "en-US",
        "User-Agent": "Instagram 101.0.0.15.120",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-FB-HTTP-Engine": "Liger",
        "Connection": "close",
    }
    try:
        async with httpx.AsyncClient(timeout=PER_CHECK_TIMEOUT) as client:
            r = await client.post(
                "https://i.instagram.com/api/v1/users/lookup/",
                content=body, headers=headers,
            )
        try:
            data = r.json()
        except Exception:
            return (None, None, None)
        if data.get("message") == "No users found":
            return (False, show_url, None)
        # Anything else (a user object, hashed contact points, etc.) => exists
        return (True, show_url, None)
    except Exception:
        return (None, None, None)


# --- Snapchat (signup phone validation) -------------------------------------

async def _chk_snapchat(cc, num):
    show_url = "https://snapchat.com"
    iso = SNAP_CC_TO_ISO.get(cc)
    if not iso:
        return (None, None, None)
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
        "Origin": "https://accounts.snapchat.com",
    }
    try:
        async with httpx.AsyncClient(timeout=PER_CHECK_TIMEOUT, follow_redirects=True) as client:
            seed = await client.get("https://accounts.snapchat.com", headers=headers)
            xsrf = seed.cookies.get("xsrf_token")
            if not xsrf:
                return (None, None, None)
            data = {
                "phone_country_code": iso,
                "phone_number": num,
                "xsrf_token": xsrf,
            }
            r = await client.post(
                "https://accounts.snapchat.com/accounts/validate_phone_number",
                headers=headers, data=data,
            )
        try:
            status = r.json().get("status_code")
        except Exception:
            return (None, None, None)
        if status == "TAKEN_NUMBER":
            return (True, show_url, None)
        if status == "OK":
            return (False, show_url, None)
        return (None, None, None)
    except Exception:
        return (None, None, None)


SERVICES = [
    ("shopping", "Amazon", _chk_amazon),
    ("social", "Instagram", _chk_instagram),
    ("social", "Snapchat", _chk_snapchat),
]


async def _safe(sem, cat, name, fn, cc, num):
    async with sem:
        try:
            res = await asyncio.wait_for(fn(cc, num), timeout=PER_CHECK_TIMEOUT)
            if isinstance(res, tuple) and len(res) == 3:
                return cat, name, res
            return cat, name, (None, None, None)
        except Exception:
            return cat, name, (None, None, None)


def _value(hit, url, extra):
    parts = []
    if hit is True:
        parts.append(f"registered ({url})" if url else "registered")
    elif hit is False:
        parts.append("not registered")
    else:
        parts.append("error")
    if extra:
        parts.append(str(extra))
    return " — ".join(parts)


async def run(session, target):
    cc, num = _parse(target)
    if not cc or not num:
        return 1, [{
            "label": "Status",
            "value": f"could not parse phone: {target}",
            "source": PARENT,
        }]

    sem = asyncio.Semaphore(CONCURRENCY)
    results = await asyncio.gather(
        *(_safe(sem, cat, name, fn, cc, num) for cat, name, fn in SERVICES)
    )

    findings = []
    for cat, name, (hit, url, extra) in results:
        if hit is not True:
            continue
        findings.append({
            "label": name,
            "value": _value(hit, url, extra),
            "source": PARENT,
            "group": cat.title(),
        })
    return 0, findings
