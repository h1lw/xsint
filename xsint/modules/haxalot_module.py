import asyncio
import time
import re
import sys
import os
import logging
import shutil
from pathlib import Path
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

# Telethon takes a "session name" (path without the .session suffix) and
# writes "<session_name>.session" next to it. Pin this to a stable path
# under the user's config dir so xsint --auth haxalot works regardless
# of where the user later runs xsint from.
_CONFIG_DIR = Path.home() / ".config" / "xsint"
SESSION_NAME = str(_CONFIG_DIR / "haxalot_session")
SESSION_FILE = SESSION_NAME + ".session"


def _ensure_session_dir():
    _CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def _migrate_legacy_session():
    """Relocate a session file dropped by an earlier xsint to the config dir.

    Older versions wrote `haxalot_session.session` next to wherever the
    user happened to be standing when they ran `xsint --auth haxalot`.
    Pick the most-recently-modified candidate and move it into the new
    canonical location so the existing login keeps working.
    """
    if os.path.isfile(SESSION_FILE):
        return
    candidates = [
        Path.cwd() / "haxalot_session.session",
        Path.home() / "haxalot_session.session",
        Path.home() / ".local" / "share" / "xsint" / "haxalot_session.session",
    ]
    existing = [p for p in candidates if p.is_file()]
    if not existing:
        return
    existing.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    try:
        _ensure_session_dir()
        shutil.move(str(existing[0]), SESSION_FILE)
        # Best-effort: clean up older duplicates so we don't migrate the
        # same files again on the next run.
        for p in existing[1:]:
            try:
                p.unlink()
            except Exception:
                pass
    except Exception:
        pass


_migrate_legacy_session()

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
    Haxalot is opt-in. The Telethon session file is the source of truth:
    if it exists and `--auth haxalot` has been run at least once, we're
    ready. We don't gate on a transient config flag — a network blip
    during a previous scan would otherwise lock the user out until they
    re-authenticated.
    """
    if os.path.isfile(SESSION_FILE):
        # Mirror this back into config so other code (and the dashboard)
        # sees the module as enabled even if a past failure cleared it.
        get_config().set("haxalot_enabled", True)
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

    _ensure_session_dir()

    # We use 'start()' here because it handles the interactive phone/code prompt automatically
    async with TelegramClient(SESSION_NAME, API_ID, API_HASH) as client:
        await client.start()

        me = await client.get_me()
        get_config().set("haxalot_enabled", True)
        print(f"\n[+] Successfully logged in as: {me.username}")
        print(f"[+] Session saved to: {SESSION_FILE}")
        print("[+] Haxalot is now ready for use.")

# Substrings the bot uses when nothing matches the query. If we see one
# of these in any reply, bail out fast instead of waiting for a report
# that's never coming.
_NO_RESULTS_MARKERS = (
    "no results found",
    "no record",
    "ничего не найдено",
    "🤷",
    "all the words in your request are found too often",
)

# Strings the bot uses for "checking your query" / busy waits — these are
# transient acks, not a final answer. Keep waiting if all we have is one
# of these.
_TRANSIENT_MARKERS = (
    "looking",
    "searching",
    "checking",
    "ищу",
    "идёт поиск",
)


def _is_no_results(text: str) -> bool:
    if not text:
        return False
    t = text.lower()
    return any(marker in t for marker in _NO_RESULTS_MARKERS)


def _is_transient(text: str) -> bool:
    if not text:
        return False
    t = text.lower()
    return any(marker in t for marker in _TRANSIENT_MARKERS)


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

        # Collect bot replies until we see something actionable: a media
        # attachment, a download-button message, or an explicit "no results"
        # reply. Plain text without any of those markers is treated as a
        # transient ack and we keep polling.
        while time.time() - start < TIMEOUT:
            try:
                got = await c.get_messages(bot, limit=10, min_id=sent.id)
            except Exception:
                await asyncio.sleep(0.3)
                continue

            for m in reversed(got):
                if m.id > sent.id and all(m.id != x.id for x in msgs):
                    msgs.append(m)

            # Fast-path "no results" — every reply is short text and at
            # least one of them carries the bot's "not found" wording.
            if msgs and any(
                _is_no_results(getattr(m, "message", "") or "") for m in msgs
            ):
                return ""

            # Found a media reply — that's our report.
            if any(m.media for m in msgs):
                break

            # Found a download-button reply — that's also actionable.
            if any(getattr(m, "buttons", None) for m in msgs):
                break

            # Otherwise wait a bit and try again.
            await asyncio.sleep(0.3)

        if not msgs:
            return ""

        # Prefer the first reply that has a media attachment or buttons.
        target = next(
            (m for m in msgs if m.media or getattr(m, "buttons", None)),
            msgs[-1],
        )

        if target.media:
            path = await c.download_media(target, file=bytes)
            return path.decode("utf-8", "ignore")

        if target.buttons:
            clicked = False
            for b in sum((target.buttons or []), []):
                if "download" in (getattr(b, "text", "") or "").lower():
                    try:
                        await target.click(text=getattr(b, "text", None))
                        clicked = True
                    except Exception:
                        await target.click()
                        clicked = True
                    break

            if clicked:
                t0 = time.time()
                while time.time() - t0 < 20:
                    try:
                        newer = await c.get_messages(bot, limit=6, min_id=target.id)
                    except Exception:
                        await asyncio.sleep(0.4)
                        continue
                    for m in reversed(newer):
                        if m.media:
                            path = await c.download_media(m, file=bytes)
                            return path.decode("utf-8", "ignore")
                        # If the post-click reply itself says "no results"
                        # (some collections emit that branch), give up.
                        if _is_no_results(getattr(m, "message", "") or ""):
                            return ""
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
        # Don't clear the config flag — a transient Telegram outage
        # shouldn't permanently lock the user out. is_ready() trusts the
        # session file directly, so we just bail quietly here.
        return 0, []

    try:
        html_content = await lookup(target)
    except Exception as e:
        return 1, [{"label": "Error", "value": str(e), "source": PARENT, "risk": "high"}]

    if not html_content:
        # No report = no breaches matched the target. Don't emit a status
        # row — the dashboard already shows "0 results" and a synthetic row
        # would just clutter the report.
        return 0, []
    
    if html_content.startswith("ERROR:"):
        return 1, [{"label": "Bot Error", "value": html_content.replace("ERROR: ", ""), "source": PARENT, "risk": "high"}]

    # parse_html_report (BeautifulSoup) and _summarize (lots of regex +
    # dict ops on potentially huge reports) are CPU-bound and sync — run
    # them in a worker thread so the live dashboard animator and any
    # other concurrent module's I/O isn't frozen during parsing.
    parsed_data = await asyncio.to_thread(parse_html_report, html_content)
    summary = await asyncio.to_thread(_summarize, parsed_data, PARENT)

    return 0, summary


# Order matters — first match wins. Plaintext password vs hashed-password
# is the most actionable distinction so it lives at the top.
_CATEGORY_RULES = [
    ("🔐 Hashes",      lambda s: "encrypted password" in s or "hash" in s or "salt" in s),
    ("🔑 Passwords",   lambda s: "password" in s),
    ("🌐 IPs",         lambda s: s.strip() == "ip" or s.endswith(" ip") or "ip address" in s),
    ("📱 Phones",      lambda s: "phone" in s or s == "mobile" or "mobile operator" in s),
    ("📧 Emails",      lambda s: "email" in s or "e-mail" in s),
    ("📍 Locations",   lambda s: any(k in s for k in [
        "address", "adres", "city", "region", "country", "state ", "postal",
        "pin code", "zip", "latitude", "longitude",
    ]) or s.strip() == "state"),
    # Aliases come before Names so "Nick" / "Username" / "Handle" don't
    # get caught by the Names rule's loose "name" substring match.
    ("👥 Aliases",     lambda s: ("nick" in s or "username" in s
                                    or "handle" in s or "login" in s)),
    ("👤 Names",       lambda s: any(k in s for k in ["full name", "surname", "name"])),
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
    "👥 Aliases",
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

# No per-category cap — caller wanted every unique value surfaced.
# Filtering / truncation is the responsibility of the renderer.
_CATEGORY_LIMIT = None


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

        shown = bucket if _CATEGORY_LIMIT is None else bucket[:_CATEGORY_LIMIT]
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
