"""Phone account enumeration across consumer services.

Adapted from megadose/ignorant (AGPL/MIT-style) — runs the three known
phone-based "is this number registered" checks (Amazon, Instagram, Snapchat)
in parallel and reports one finding per registered hit.

Each check returns (hit: bool|None, url: str|None, extra: str|None).
"""
import asyncio
import html
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

# E.164 country code -> (regional Amazon domain, openid.assoc_handle)
_AMAZON_REGIONS = {
    "1":   ("amazon.com",     "usflex"),
    "44":  ("amazon.co.uk",   "gbflex"),
    "49":  ("amazon.de",      "deflex"),
    "33":  ("amazon.fr",      "frflex"),
    "39":  ("amazon.it",      "itflex"),
    "34":  ("amazon.es",      "esflex"),
    "91":  ("amazon.in",      "inflex"),
    "81":  ("amazon.co.jp",   "jpflex"),
    "86":  ("amazon.cn",      "cnflex"),
    "52":  ("amazon.com.mx",  "mxflex"),
    "55":  ("amazon.com.br",  "brflex"),
    "61":  ("amazon.com.au",  "auflex"),
    "31":  ("amazon.nl",      "nlflex"),
    "46":  ("amazon.se",      "seflex"),
    "48":  ("amazon.pl",      "plflex"),
    "90":  ("amazon.com.tr",  "trflex"),
    "971": ("amazon.ae",      "aeflex"),
    "966": ("amazon.sa",      "saflex"),
    "20":  ("amazon.eg",      "egflex"),
    "32":  ("amazon.com.be",  "beflex"),
    "65":  ("amazon.sg",      "sgflex"),
}


async def _chk_amazon(cc, num):
    """Probe Amazon's regional unified-claim flow with a phone number.

    Modern Amazon signin routes phone-number identifiers through
    /ax/claim with claimType=phoneNumber + countryCode=<ISO>. The response
    redirects to /ax/aaut/verify/... (or /ap/signin/...) when the account
    exists, and stays on the claim page (often with an inline error) when
    it does not. Falls back to detecting a password input element.
    """
    import re as _re
    domain, assoc = _AMAZON_REGIONS.get(cc, ("amazon.com", "usflex"))
    iso = SNAP_CC_TO_ISO.get(cc)
    if not iso:
        return (None, None, None)
    show_url = f"https://{domain}"
    base = f"https://www.{domain}"
    return_to = urllib.parse.quote(f"{base}/", safe="")
    signin_url = (
        f"{base}/ap/signin?openid.pape.max_auth_age=0"
        f"&openid.return_to={return_to}"
        f"&openid.identity=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select"
        f"&openid.assoc_handle={assoc}&openid.mode=checkid_setup"
        f"&openid.claimed_id=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select"
        f"&openid.ns=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0"
    )
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    try:
        async with httpx.AsyncClient(timeout=PER_CHECK_TIMEOUT, follow_redirects=True) as client:
            r = await client.get(signin_url, headers=headers)
            html = r.text
            landed_url = str(r.url)

            # Pull every hidden input the form provides — picks up metadata1,
            # anti-csrftoken-a2z, appAction, claimCollectionWorkflow, etc.
            data = {}
            for tag in _re.findall(r'<input[^>]+>', html):
                m_name = _re.search(r'name="([^"]+)"', tag)
                m_val = _re.search(r'value="([^"]*)"', tag)
                if m_name:
                    data[m_name.group(1)] = m_val.group(1) if m_val else ""

            # Form action — usually a relative path on the same host.
            # html.unescape collapses &amp; etc. so we don't end up POSTing
            # to a literal-ampersand URL that Amazon 404s.
            import html as _htmllib
            m_action = _re.search(r'<form[^>]+action="([^"]+)"', html)
            action = _htmllib.unescape(m_action.group(1)) if m_action else "/ap/signin/"
            if action.startswith("/"):
                action = base + action
            elif not action.startswith("http"):
                action = landed_url

            # Override the phone-claim fields. Form ships these as empty
            # placeholder hidden inputs that JS populates client-side, so we
            # have to assign rather than setdefault.
            data["email"] = f"+{cc}{num}"
            data["password"] = data.get("password", "")
            data["claimType"] = "phoneNumber"
            data["countryCode"] = iso
            data["isServerSideRouting"] = "true"
            data.setdefault("claimCollectionWorkflow", "unified")

            post_headers = dict(headers)
            post_headers["Content-Type"] = "application/x-www-form-urlencoded"
            post_headers["Origin"] = base
            post_headers["Referer"] = landed_url

            r2 = await client.post(action, data=data, headers=post_headers, follow_redirects=False)

            # 302 to a password / verify URL = recognized account.
            if r2.status_code in (301, 302, 303, 307, 308):
                loc = r2.headers.get("location", "") or ""
                if any(p in loc for p in ("/ax/aaut/verify", "/ap/signin", "/ap/mfa", "/ap/cvf")):
                    return (True, show_url, None)
                # Some regions redirect back to the claim page on miss.
                if "/ax/claim" in loc:
                    return (False, show_url, None)
                return (None, show_url, None)

            text = r2.text
            if (
                'id="auth-password-missing-alert"' in text
                or 'id="ap_password"' in text
                or ('name="password"' in text and 'type="password"' in text)
            ):
                return (True, show_url, None)
            return (False, show_url, None)
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
