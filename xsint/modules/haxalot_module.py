import asyncio
import time
import re
import sys
import os
import logging
from bs4 import BeautifulSoup, NavigableString
from telethon import TelegramClient
from xsint.config import get_config

# Keep Telethon retries/log noise out of CLI report output.
logging.getLogger("telethon").setLevel(logging.ERROR)

# Provided Credentials
API_ID = 23268457
API_HASH = "6f9d49402bd4eee4de800dd861d7c549"
BOT = "haxalotBot"
TIMEOUT = 25
SESSION_NAME = "haxalot_session"

INFO = {
    "free": ["email", "username", "phone", "ip"],
    "paid": [],
    "returns": ["breaches", "passwords", "pii"],
    "themes": {
        "Haxalot":   {"color": "cyan",    "icon": "🤖"},
        "Breach":    {"color": "red",     "icon": "🔓"},
        "Password":  {"color": "yellow",  "icon": "🔑"},
        "Info":      {"color": "white",   "icon": "ℹ️"},
    }
}

def is_ready():
    """
    Module readiness gate used by the engine.
    Haxalot is opt-in and requires both:
    - successful setup marker in xsint config
    - local Telegram session file
    """
    cfg = get_config()
    if not cfg.get("haxalot_enabled", False):
        return False, "run xsint --auth haxalot"
    session_file = SESSION_NAME + ".session"
    if os.path.isfile(session_file):
        return True, ""
    return False, "run xsint --auth haxalot"

async def check_auth_state():
    """Non-interactive check to see if we have a valid session."""
    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
    try:
        await asyncio.wait_for(client.connect(), timeout=4)
        is_auth = await asyncio.wait_for(client.is_user_authorized(), timeout=4)
        await asyncio.wait_for(client.disconnect(), timeout=2)
        return is_auth
    except Exception:
        try:
            await asyncio.wait_for(client.disconnect(), timeout=1)
        except Exception:
            pass
        return False

async def setup():
    """
    Interactive setup routine called by --auth haxalot
    """
    print("\n[+] Haxalot Module Setup (Telegram)")
    print("-----------------------------------")
    print("This will create a local session file to authenticate with Telegram.")
    print("You will need your phone number and the OTP code sent to your Telegram app.\n")
    
    # We use 'start()' here because it handles the interactive phone/code prompt automatically
    async with TelegramClient(SESSION_NAME, API_ID, API_HASH) as client:
        await client.start()
        
        me = await client.get_me()
        get_config().set("haxalot_enabled", True)
        print(f"\n[+] Successfully logged in as: {me.username}")
        print(f"[+] Session saved to: {os.path.abspath(SESSION_NAME + '.session')}")
        print("[+] Haxalot is now ready for use.")

async def lookup(query: str) -> str:
    # Connect using the existing session
    async with TelegramClient(SESSION_NAME, API_ID, API_HASH) as c:
        if not await c.is_user_authorized():
            return "ERROR: Not authorized. Run 'python3 -m xsint --auth haxalot'"

        try:
            bot = await c.get_entity(BOT)
        except ValueError:
            return "ERROR: Bot not found (Account may be limited)"
            
        sent = await c.send_message(BOT, query)
        start = time.time()
        msgs = []
        
        while len(msgs) < 2 and time.time() - start < TIMEOUT:
            try:
                got = await c.get_messages(bot, limit=10, min_id=sent.id)
            except Exception:
                await asyncio.sleep(0.3); continue
            
            for m in reversed(got):
                if m.id > sent.id and all(m.id != x.id for x in msgs):
                    msgs.append(m)
            await asyncio.sleep(0.3)
        
        if not msgs: return ""

        target = msgs[1] if len(msgs) > 1 else msgs[-1]
        
        if target.media:
            path = await c.download_media(target, file=bytes)
            return path.decode("utf-8", "ignore")

        if target.buttons:
            clicked = False
            for b in sum((target.buttons or []), []):
                if "download" in (getattr(b, "text", "") or "").lower():
                    try: await target.click(text=getattr(b, "text", None)); clicked = True
                    except: await target.click(); clicked = True
                    break
            
            if clicked:
                t0 = time.time()
                while time.time() - t0 < 20:
                    try:
                        newer = await c.get_messages(bot, limit=6, min_id=target.id)
                    except Exception: await asyncio.sleep(0.4); continue
                    for m in reversed(newer):
                        if m.media:
                            path = await c.download_media(m, file=bytes)
                            return path.decode("utf-8", "ignore")
                    await asyncio.sleep(0.4)
        return ""

def parse_html_report(html: str) -> dict:
    def _normalize_key(key_raw: str) -> str:
        clean = re.sub(r"[:：]\s*$", "", key_raw).strip()
        return clean.title()

    def _extract_value(b_tag) -> str:
        value_parts = []
        for sibling in b_tag.next_siblings:
            if getattr(sibling, 'name', None) == 'b': break
            if getattr(sibling, 'name', None) == 'code':
                value_parts.append(sibling.get_text(strip=True))
                break
            if isinstance(sibling, NavigableString):
                part = str(sibling).strip()
                if part: value_parts.append(part)
                break
        return " ".join(value_parts)

    if not html: return {"sections": []}
    soup = BeautifulSoup(html, "lxml")
    report = {"sections": []}
    
    for block in soup.select("div.block"):
        title_el = block.select_one(".block-title")
        block_text = block.select_one(".block-text")
        if not (title_el and block_text): continue
        
        raw_pairs = []
        for b_tag in block_text.find_all("b"):
            key = _normalize_key(b_tag.get_text())
            value = _extract_value(b_tag)
            if key and value: raw_pairs.append((key, value))

        items = []
        if raw_pairs:
            current_item = {}
            for k, v in raw_pairs:
                if k in current_item:
                    items.append(current_item)
                    current_item = {}
                current_item[k] = v
            items.append(current_item)

        if items:
            raw_title = title_el.get_text(" ", strip=True)
            section_title = re.sub(r'[^\w .-]+', '', raw_title).strip()
            report["sections"].append({"section_title": section_title, "items": items})
    return report

async def run(session, target):
    results = []
    PARENT = "Haxalot"
    
    is_auth = await check_auth_state()
    if not is_auth:
        get_config().set("haxalot_enabled", False)
        return 0, [{"label": "Status", "value": "Module locked (Run --auth haxalot)", "source": PARENT, "risk": "low"}]

    try:
        html_content = await lookup(target)
    except Exception as e:
        return 1, [{"label": "Error", "value": str(e), "source": PARENT, "risk": "high"}]

    if not html_content:
        return 0, [{"label": "Status", "value": "No report found", "source": PARENT, "risk": "low"}]
    
    if html_content.startswith("ERROR:"):
        return 1, [{"label": "Bot Error", "value": html_content.replace("ERROR: ", ""), "source": PARENT, "risk": "high"}]

    parsed_data = parse_html_report(html_content)

    # Aggregate across breaches: bucket every (label, value) pair into a
    # human-readable category, dedupe values, and remember which breaches
    # each value came from. Easier to skim than the raw per-breach dump.
    return 0, _summarize(parsed_data, PARENT)


# Order matters — first match wins. Plaintext password vs hashed-password
# is the most actionable distinction so it lives at the top.
_CATEGORY_RULES = [
    ("🔐 Hashes",      lambda s: "encrypted password" in s or "hash" in s or "salt" in s),
    ("🔑 Passwords",   lambda s: "password" in s),
    ("🌐 IPs",         lambda s: s.strip() == "ip" or s.endswith(" ip") or "ip address" in s),
    ("📱 Phones",      lambda s: "phone" in s or s == "mobile" or "mobile operator" in s),
    ("📧 Emails",      lambda s: "email" in s or "e-mail" in s),
    ("📍 Locations",   lambda s: any(k in s for k in [
        "address", "adres", "city", "region", "country", "stat", "postal",
        "pin code", "zip", "latitude", "longitude",
    ])),
    ("👤 Names",       lambda s: any(k in s for k in ["full name", "surname", "name", "nick"])),
    ("📆 Dates",       lambda s: "date" in s or "activity" in s or "registration" in s),
    ("🏢 Companies",   lambda s: "company" in s),
    ("🔗 Links",       lambda s: any(k in s for k in ["link", "website", "url", "app ("])),
    ("💻 Devices",     lambda s: any(k in s for k in ["browser", "operational system", "user agent"])),
    ("💸 Financial",   lambda s: any(k in s for k in [
        "sum", "credit", "bank", "product", "number of orders",
    ])),
    ("🆔 Identifiers", lambda s: s.endswith("id") or " id" in s),
    ("📝 Content",     lambda s: any(k in s for k in ["comment", "rating", "text"])),
]

# How categories appear in the rendered report (most-actionable first).
_CATEGORY_ORDER = [
    "🔑 Passwords",
    "🔐 Hashes",
    "👤 Names",
    "📍 Locations",
    "📱 Phones",
    "📧 Emails",
    "🌐 IPs",
    "💻 Devices",
    "🔗 Links",
    "💸 Financial",
    "🏢 Companies",
    "🆔 Identifiers",
    "📆 Dates",
    "📝 Content",
    "📋 Other",
]

# Per-category cap so a noisy breach doesn't drown the report.
_CATEGORY_LIMIT = 20


def _classify(label: str) -> str:
    s = label.lower()
    for cat, match in _CATEGORY_RULES:
        if match(s):
            return cat
    return "📋 Other"


def _category_priority(cat: str) -> int:
    try:
        return _CATEGORY_ORDER.index(cat)
    except ValueError:
        return len(_CATEGORY_ORDER)


def _format_breaches(breaches: dict) -> str:
    items = sorted(breaches.items(), key=lambda kv: (-kv[1], kv[0].lower()))
    parts = []
    for name, count in items[:3]:
        parts.append(f"{name} ×{count}" if count > 1 else name)
    if len(items) > 3:
        parts.append(f"+{len(items) - 3} more")
    return ", ".join(parts) or "Unknown"


def _risk_for(category: str) -> str:
    if category in {"🔑 Passwords", "🔐 Hashes"}:
        return "critical"
    if category in {"📱 Phones", "🌐 IPs", "📍 Locations", "💸 Financial"}:
        return "high"
    if category in {"👤 Names", "📧 Emails", "🆔 Identifiers"}:
        return "medium"
    return "low"


def _summarize(parsed_data: dict, parent: str) -> list:
    # value -> {"category": str, "breaches": {breach_name: count}}
    by_value: dict = {}
    breach_names: list = []

    for section in parsed_data.get("sections", []):
        breach = (section.get("section_title") or "Unknown").strip()
        items = section.get("items", []) or []
        if not items:
            continue
        breach_names.append(breach)

        for item in items:
            for k, v in item.items():
                value = str(v).strip()
                if not value or value.lower() in {"none", "n/a", "null"}:
                    continue
                category = _classify(k)
                slot = by_value.setdefault(
                    value,
                    {"category": category, "breaches": {}},
                )
                # If the same literal value shows up under different field
                # labels across breaches, keep the most specific category.
                if _category_priority(category) < _category_priority(slot["category"]):
                    slot["category"] = category
                slot["breaches"][breach] = slot["breaches"].get(breach, 0) + 1

    results = []

    # Top-level summary line listing every breach the target appears in.
    if breach_names:
        unique = sorted(set(breach_names))
        results.append({
            "label": "Sources",
            "value": f"{len(unique)} breaches: " + ", ".join(unique),
            "source": parent,
            "group": "📋 Summary",
            "risk": "medium",
        })

    # Bucket deduped values by category.
    by_category: dict = {}
    for value, slot in by_value.items():
        by_category.setdefault(slot["category"], []).append((value, slot["breaches"]))

    for category in _CATEGORY_ORDER:
        bucket = by_category.get(category)
        if not bucket:
            continue
        # Sort by total occurrences (most reused first), then alphabetically.
        bucket.sort(key=lambda vb: (-sum(vb[1].values()), vb[0].lower()))

        shown = bucket[:_CATEGORY_LIMIT]
        for value, breaches in shown:
            results.append({
                "label": _format_breaches(breaches),
                "value": value,
                "source": parent,
                "group": category,
                "risk": _risk_for(category),
            })
        remaining = len(bucket) - len(shown)
        if remaining > 0:
            results.append({
                "label": "More",
                "value": f"+{remaining} more unique values",
                "source": parent,
                "group": category,
                "risk": "low",
            })

    return results
