"""Output formatters for xsint scan reports.

Four flavors:
  raw    — plain `source / group / label : value` dump (default, machine-skimmable)
  json   — JSON encode of the full report (pipeable, machine-readable)
  html   — self-contained static HTML page (single file, embedded CSS)
  pretty — synthesized identity dossier (deduped, person-oriented summary)
"""

import html as _html
import json
import re
import time


def print_results(report, target=None, fmt="raw"):
    if fmt == "json":
        _print_json(report, target)
    elif fmt == "html":
        _print_html(report, target)
    elif fmt == "pretty":
        _print_pretty(report, target)
    else:
        _print_raw(report)


# ---------- shared helpers for pretty + html (synthesis layer) ----------

def _email_local(target):
    if not target or "@" not in str(target):
        return ""
    return str(target).split("@", 1)[0].lower()


def _name_tokens(s):
    """Return lowercase 2+ char alpha tokens — used for fuzzy name matching."""
    return re.findall(r"[a-zà-ÿ]{2,}", s.lower())


def _name_matches_target(name, target_local):
    """Does this name plausibly belong to the target?"""
    if not name or not target_local:
        return False
    target_local = re.sub(r"\d+", "", target_local).lower()
    if not target_local:
        return False
    for tok in _name_tokens(name):
        if tok in target_local or target_local in tok:
            return True
    return False


_CARRIER_NAMES = {
    "vodafone", "vodafone india", "airtel", "bharti airtel", "reliance jio",
    "reliance", "reliance mobile", "reliance mobile gsm", "idea cellular",
    "idea", "aircel", "bsnl", "mts india", "tata", "tata docomo", "tata cdma",
    "telenor", "uninor", "videocon", "lycamobile", "verizon", "at&t", "att",
    "t-mobile", "sprint", "tmobile", "orange", "ee", "o2", "vodafone uk",
    "telefonica", "movistar", "claro", "telcel", "rogers", "bell", "telus",
}


def _looks_like_phone_number(s):
    """Strict phone-shape check — keeps real numbers, drops carrier names."""
    digits = re.sub(r"\D", "", s)
    if 7 <= len(digits) <= 15:
        # Reject strings dominated by alpha (e.g. "Reliance Jio" with stray digits).
        alpha = sum(c.isalpha() for c in s)
        return alpha < len(digits)
    return False


def _looks_like_carrier(s):
    return s.lower().strip() in _CARRIER_NAMES


_LOCATION_NOISE = {
    "active", "inactive", "complete", "address", "consumer", "unknown",
    "lead", "member", "n/a", "none", "null", "default", "true", "false",
    "0", "1", "yes", "no",
}


def _is_meaningful_location(s):
    s = s.strip()
    if not s:
        return False
    # Pure numeric / lat-lng noise.
    if re.match(r"^[\-\d.,\s]+$", s):
        return False
    # Single 2-letter token (US state codes alone are noise without context).
    if re.match(r"^[A-Z]{2}$", s):
        return False
    if s.lower() in _LOCATION_NOISE:
        return False
    return True


def _is_ip(s):
    return bool(re.match(r"^\d{1,3}(\.\d{1,3}){3}$", s.strip()))


# ---------- raw ----------

def _print_raw(report):
    results = report.get("results", [])
    target_type = str(report.get("type", "unknown")).upper()
    error = report.get("error")

    if error:
        print(f"type   : {target_type}")
        print("status : aborted")
        print(f"error  : {error}")
        return

    if not results:
        print(f"type     : {target_type}")
        print("status   : completed")
        print("findings : 0")
        return

    groups = {}
    for item in results:
        groups.setdefault(item.get("source", "unknown"), []).append(item)

    print(f"type     : {target_type}")
    print(f"findings : {len(results)}")
    print(f"sources  : {len(groups)}")
    print()

    for source in sorted(groups):
        items = groups[source]
        print(f"{source} ({len(items)})")
        max_label = max(len(_label(i)) for i in items)
        for item in items:
            label = _label(item).ljust(max_label)
            value = str(item.get("value", "N/A"))
            print(f"  {label} : {value}")
        print()


def _label(item):
    label = str(item.get("label", "N/A"))
    group = item.get("group")
    return f"{group} / {label}" if group else label


# ---------- json ----------

def _print_json(report, target):
    payload = {
        "target": target,
        "type": report.get("type"),
        "scanned_at": int(time.time()),
        "findings": len(report.get("results", []) or []),
        "results": report.get("results", []) or [],
        "themes": report.get("themes") or {},
        "error": report.get("error"),
    }
    print(json.dumps(payload, indent=2, default=str, ensure_ascii=False))


# ---------- html ----------

_HTML_CSS = """
:root { color-scheme: light dark; }
* { box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, sans-serif;
       max-width: 1040px; margin: 2rem auto; padding: 0 1.25rem;
       color: #1f2328; background: #fff; line-height: 1.5; }
header.report-head { border-bottom: 2px solid #d0d7de; padding-bottom: 1rem; margin-bottom: 1.5rem; }
header.report-head h1 { margin: 0 0 .5rem; font-size: 1.5rem; font-weight: 600; letter-spacing: -.01em; }
header.report-head .meta { color: #57606a; font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
                            font-size: .85rem; line-height: 1.6; }
section.dossier { margin-bottom: 1.6rem; }
section.dossier > h2 { font-size: 1rem; font-weight: 600; margin: 0 0 .55rem;
                       padding-bottom: .35rem; border-bottom: 1px solid #d8dee4;
                       text-transform: uppercase; letter-spacing: .05em; color: #57606a; }
section.dossier > h2 .count { color: #8b949e; font-weight: 400; font-size: .8rem;
                              margin-left: .4rem; text-transform: none; letter-spacing: 0; }
.row { display: flex; gap: 1rem; padding: .25rem 0; }
.row + .row { border-top: 1px dashed #eaeef2; }
.row .label { flex: 0 0 9rem; color: #57606a; font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
              font-size: .82rem; padding-top: .15rem; }
.row .value { flex: 1; min-width: 0; }
.row .value ul { margin: 0; padding: 0; list-style: none; }
.row .value li { padding: .15rem 0; word-break: break-word; }
.row .value li .attr { color: #8b949e; font-size: .8rem; margin-left: .5rem; }
.row .value a { color: #0969da; text-decoration: none; word-break: break-all; }
.row .value a:hover { text-decoration: underline; }
.row .value .mono { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: .85rem; }
.row .value .secret { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: .85rem;
                       background: #fff8c5; padding: 1px 6px; border-radius: 3px; }
.row .value .hash { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: .8rem;
                    color: #57606a; }
.tag { display: inline-block; padding: 1px 8px; margin: 1px 4px 1px 0;
       background: #ddf4ff; color: #0969da; border-radius: 12px; font-size: .8rem; }
.breach-tag { background: #ffebe9; color: #cf222e; }
footer { margin-top: 2.5rem; color: #8b949e; font-size: .75rem; text-align: center;
         border-top: 1px solid #d8dee4; padding-top: .75rem; }

@media (prefers-color-scheme: dark) {
  body { color: #c9d1d9; background: #0d1117; }
  header.report-head { border-color: #30363d; }
  header.report-head .meta { color: #8b949e; }
  section.dossier > h2 { border-color: #30363d; color: #8b949e; }
  .row + .row { border-color: #21262d; }
  .row .label { color: #8b949e; }
  .row .value li .attr { color: #6e7681; }
  .row .value a { color: #58a6ff; }
  .row .value .secret { background: #3a2d00; color: #f0883e; }
  .row .value .hash { color: #8b949e; }
  .tag { background: #1f3a5e; color: #58a6ff; }
  .breach-tag { background: #5c1a1a; color: #ff7b72; }
  footer { color: #6e7681; border-color: #30363d; }
}
"""


def _print_html(report, target):
    """Render the identity dossier as a styled HTML page.

    Same layout as --pretty (PERSON / ACCOUNTS / CONTACT / LOCATIONS /
    BREACH EXPOSURE / CREDENTIALS LEAKED / ACTIVITY / LINKS) so the
    formats stay aligned — the user reads either one and sees the same
    information, just rendered differently.
    """
    results = report.get("results", []) or []
    target_type = str(report.get("type", "unknown")).upper()
    target_str = target or "(unknown)"
    when = time.strftime("%Y-%m-%d %H:%M:%S %Z", time.localtime())
    error = report.get("error")
    sources = sorted({r.get("source") for r in results if r.get("source")})

    parts = [
        "<!DOCTYPE html>",
        '<html lang="en"><head>',
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        f"<title>xsint identity report — {_html.escape(target_str)}</title>",
        f"<style>{_HTML_CSS}</style>",
        "</head><body>",
        '<header class="report-head">',
        "<h1>xsint identity report</h1>",
        '<div class="meta">',
        f"target  : <strong>{_html.escape(target_str)}</strong><br>",
        f"type    : {_html.escape(target_type)}<br>",
        f"scanned : {_html.escape(when)}<br>",
        f"findings: {len(results)} across {len(sources)} source"
        + ("s" if len(sources) != 1 else ""),
        "</div></header>",
    ]

    if error:
        parts.append(
            f'<section class="dossier"><h2>Error</h2>'
            f'<pre>{_html.escape(str(error))}</pre></section>'
        )
    elif not results:
        parts.append('<section class="dossier"><p>No findings.</p></section>')
    else:
        bins = _bin_findings(results, target=target)

        # IDENTITY
        identity_rows = []
        if bins["names"]:
            items = []
            for name, breaches, auth in bins["names"]:
                if auth:
                    items.append(
                        f'{_html.escape(name)}'
                        f' <span class="attr">[{_html.escape(auth)}]</span>'
                    )
                elif breaches:
                    items.append(
                        f'{_html.escape(name)}'
                        f' <span class="attr">[{_html.escape(", ".join(breaches))}]</span>'
                    )
                else:
                    items.append(_html.escape(name))
            identity_rows.append(("name", _html_list(items)))
        if bins["photos"]:
            identity_rows.append((
                "photo",
                _html_list([
                    f'<a href="{_html.escape(v)}" target="_blank" rel="noopener">'
                    f'{_html.escape(v)}</a>'
                    for v, _ in bins["photos"]
                ]),
            ))
        for kind, value, src in bins["ids"]:
            identity_rows.append((
                kind.lower(),
                f'<span class="mono">{_html.escape(str(value))}</span>'
                f' <span class="attr">[{_html.escape(src)}]</span>',
            ))
        if identity_rows:
            parts.append(_html_section("Identity", identity_rows))

        # ALIASES
        if bins["aliases"]:
            parts.append(_html_section("Aliases", [
                ("handles", _html_attributed_list_from_breaches(bins["aliases"])),
            ]))

        # REGISTERED ACCOUNTS
        if bins["registered_on"]:
            services = sorted({s for s, _ in bins["registered_on"]}, key=str.lower)
            tags = "".join(
                f'<span class="tag">{_html.escape(s)}</span>' for s in services
            )
            parts.append(_html_section(
                f"Registered accounts ({len(services)})",
                [("services", tags)],
            ))

        # CONTACT
        contact_rows = []
        if bins["phones"]:
            contact_rows.append(("phones",
                _html_attributed_list_from_breaches(bins["phones"])))
        if bins["alt_emails"]:
            contact_rows.append(("emails",
                _html_attributed_list_from_breaches(bins["alt_emails"])))
        if bins["carriers"]:
            contact_rows.append(("carriers",
                _html_attributed_list_from_breaches(bins["carriers"])))
        if bins["ips"]:
            contact_rows.append(("ip seen",
                _html_list([
                    f'<span class="mono">{_html.escape(v)}</span>'
                    f' <span class="attr">[{_html.escape(", ".join(b))}]</span>'
                    for v, b in bins["ips"]
                ])))
        if contact_rows:
            parts.append(_html_section("Contact", contact_rows))

        # LOCATIONS
        if bins["locations"]:
            parts.append(_html_section(
                f"Locations ({len(bins['locations'])})",
                [("seen", _html_attributed_list_from_breaches(bins["locations"]))],
            ))

        # BREACH HISTORY
        if bins["breaches"]:
            tags = "".join(
                f'<span class="tag breach-tag">'
                f'{_html.escape(name)}'
                f'{(" — " + _html.escape(date)) if date else ""}'
                f' <span class="attr">[{_html.escape(src)}]</span>'
                f'</span>'
                for name, date, src in bins["breaches"]
            )
            parts.append(_html_section(
                f"Breach history ({len(bins['breaches'])})",
                [("breaches", tags)],
            ))

        # CREDENTIALS LEAKED
        cred_rows = []
        if bins["passwords"]:
            cred_rows.append((f"passwords ({len(bins['passwords'])})",
                _html_list([
                    f'<span class="secret">{_html.escape(v)}</span>'
                    f' <span class="attr">[{_html.escape(", ".join(b))}]</span>'
                    for v, b in bins["passwords"]
                ])
            ))
        if bins["hashes"]:
            cred_rows.append((f"hashes ({len(bins['hashes'])})",
                _html_list([
                    f'<span class="hash">{_html.escape(v)}</span>'
                    f' <span class="attr">[{_html.escape(", ".join(b))}]</span>'
                    for v, b in bins["hashes"]
                ])
            ))
        if cred_rows:
            parts.append(_html_section("Credentials leaked", cred_rows))

        # ACTIVITY
        if bins["activity"] or bins["dates"]:
            activity_items = [_html.escape(label) for label, _src in bins["activity"]]
            for label, val, breach in bins["dates"]:
                activity_items.append(
                    f'<span class="attr">{_html.escape(breach)}:</span> '
                    f'{_html.escape(label)}: <span class="mono">{_html.escape(val)}</span>'
                )
            if activity_items:
                parts.append(_html_section("Activity",
                    [("events", _html_list(activity_items))]))

        # LINKS
        if bins["links"]:
            parts.append(_html_section(f"Links ({len(bins['links'])})", [
                ("seen",
                 _html_list([
                     f'<span class="attr">{_html.escape(label)}:</span> '
                     f'<a href="{_html.escape(url)}" target="_blank" rel="noopener">'
                     f'{_html.escape(url)}</a>'
                     for label, url in bins["links"]
                 ]))
            ]))

        # OTHER
        if bins["other"]:
            parts.append(_html_section("Other", [
                ("misc",
                 _html_list([
                     f'<span class="attr">{_html.escape(str(a))}:</span> '
                     f'{_linkify_html(str(b))} '
                     f'<span class="attr">[{_html.escape(str(c))}]</span>'
                     for a, b, c in bins["other"]
                 ]))
            ]))

    parts.append("<footer>generated by xsint</footer>")
    parts.append("</body></html>")
    print("\n".join(parts))


def _html_section(title, rows):
    body = []
    body.append(f'<section class="dossier"><h2>{_html.escape(title)}</h2>')
    for label, value in rows:
        body.append(
            f'<div class="row"><div class="label">{_html.escape(label)}</div>'
            f'<div class="value">{value}</div></div>'
        )
    body.append("</section>")
    return "\n".join(body)


def _html_list(items):
    if not items:
        return ""
    lis = "".join(f"<li>{i}</li>" for i in items)
    return f"<ul>{lis}</ul>"


def _html_attributed_list(items):
    """Format a list of (value, attribution) into <li> entries."""
    lis = "".join(
        f'<li>{_html.escape(value)}'
        f' <span class="attr">({_html.escape(attr)})</span></li>'
        for value, attr in items
    )
    return f"<ul>{lis}</ul>"


def _html_attributed_list_from_breaches(items):
    """Format a list of (value, [breach_list]) into <li> entries."""
    lis = []
    for value, breaches in items:
        attr = (
            f' <span class="attr">[{_html.escape(", ".join(breaches))}]</span>'
            if breaches else ""
        )
        lis.append(f'<li>{_html.escape(value)}{attr}</li>')
    return f"<ul>{''.join(lis)}</ul>"


def _linkify_html(text):
    escaped = _html.escape(text)
    return re.sub(
        r"(https?://[^\s)>\"]+)",
        lambda m: f'<a href="{m.group(1)}" rel="noopener noreferrer" target="_blank">{m.group(1)}</a>',
        escaped,
    )


# ---------- pretty (identity dossier) ----------

def _print_pretty(report, target):
    target_type = str(report.get("type", "unknown")).lower()
    error = report.get("error")
    width = 78

    # Color codes — only when stdout is a real TTY; piped/file output
    # stays clean.
    is_tty = __import__("sys").stdout.isatty()
    BOLD = "\033[1m" if is_tty else ""
    DIM = "\033[2m" if is_tty else ""
    YEL = "\033[33m" if is_tty else ""
    GRN = "\033[32m" if is_tty else ""
    RED = "\033[31m" if is_tty else ""
    RST = "\033[0m" if is_tty else ""

    # Header banner
    print()
    print(f"  {BOLD}IDENTITY REPORT{RST}")
    print(f"  {target or '(unknown)'}")
    print(f"  {DIM}{'─' * (width - 4)}{RST}")

    if error:
        print(f"  status    {RED}aborted{RST}")
        print(f"  error     {error}")
        print()
        return

    results = report.get("results", []) or []
    sources = sorted({r.get("source") for r in results if r.get("source")})

    if not results:
        print(f"  status    {DIM}no intel found{RST}")
        print()
        return

    bins = _bin_findings(results, target=target)

    print(f"  type      {target_type}")
    print(f"  scanned   {time.strftime('%Y-%m-%d %H:%M', time.localtime())}")
    scope = (
        f"{len(sources)} sources · {len(bins['breaches'])} breaches · "
        f"{len(bins['passwords'])} passwords · {len(bins['hashes'])} hashes"
    )
    print(f"  scope     {DIM}{scope}{RST}")
    print()

    # ── Local helpers wired to the live color flags ──
    def _section(title, count=None):
        heading = title.upper()
        if count is not None:
            heading += f"  ·  {count}"
        print()
        print(f"  {BOLD}{heading}{RST}")
        print(f"  {DIM}{'─' * len(heading)}{RST}")

    def _row(label, value, attr=None, value_color=""):
        """Emit a single row.  Attr is rendered dim, right-aligned when it
        fits on the same line; otherwise it falls onto a continuation line."""
        label_w = 11
        indent = "  "
        label_str = (label or "").ljust(label_w)
        v = str(value)
        full_value = f"{value_color}{v}{RST}" if value_color else v

        if not attr:
            print(f"{indent}{label_str}{full_value}")
            return

        # Visible-width check (ignores ANSI codes).
        bare = f"{indent}{label_str}{v}  {attr}"
        if len(bare) <= width:
            pad = width - len(f"{indent}{label_str}{v}{attr}")
            print(f"{indent}{label_str}{full_value}{' ' * pad}{DIM}{attr}{RST}")
        else:
            print(f"{indent}{label_str}{full_value}")
            print(f"{indent}{' ' * label_w}{DIM}└─ {attr}{RST}")

    def _multirow(label, items):
        """First item gets the label, rest get blank label."""
        if not items:
            return
        first = True
        for entry in items:
            if isinstance(entry, tuple):
                value, attr = entry
            else:
                value, attr = entry, None
            _row(label if first else "", value, attr)
            first = False

    # ── Identity ─────────────────────────────────
    id_items = []
    for name, breaches, auth in bins["names"]:
        attr = auth if auth else (", ".join(breaches) if breaches else None)
        id_items.append((name, attr))
    if id_items or bins["photos"] or bins["ids"]:
        _section("Identity")
        if id_items:
            _multirow("name", id_items)
        for url, _ in bins["photos"]:
            _row("photo", url)
        for kind, value, src in bins["ids"]:
            _row(kind.lower(), value, src)

    # ── Aliases ──────────────────────────────────
    if bins["aliases"]:
        _section("Aliases", count=len(bins["aliases"]))
        for value, breaches in bins["aliases"]:
            attr = ", ".join(breaches) if breaches else None
            _row("", value, attr)

    # ── Registered accounts ──────────────────────
    if bins["registered_on"]:
        services = sorted({s for s, _ in bins["registered_on"]}, key=str.lower)
        _section("Registered accounts", count=len(services))
        for line in _wrap(" · ".join(services), width - 4):
            print(f"  {line}")

    # ── Contact ──────────────────────────────────
    contact_blocks = [
        ("phones",   bins["phones"]),
        ("emails",   bins["alt_emails"]),
        ("ip seen",  bins["ips"]),
        ("carriers", bins["carriers"]),
    ]
    if any(b for _, b in contact_blocks):
        _section("Contact")
        for label, items in contact_blocks:
            if not items:
                continue
            _multirow(label, [
                (v, ", ".join(b) if b else None) for v, b in items
            ])

    # ── Locations ────────────────────────────────
    if bins["locations"]:
        _section("Locations", count=len(bins["locations"]))
        _multirow("seen", [
            (v, ", ".join(b) if b else None) for v, b in bins["locations"]
        ])

    # ── Breach history ───────────────────────────
    if bins["breaches"]:
        _section("Breach history", count=len(bins["breaches"]))
        dated, undated = [], []
        for name, date, src in bins["breaches"]:
            if date:
                dated.append((date, name, src))
            else:
                undated.append((name, src))
        dated.sort(reverse=True)
        for date, name, src in dated:
            _row("", f"{date}  {name}", src)
        if dated and undated:
            print()
        for name, src in undated:
            _row("", name, src)

    # ── Credentials leaked ───────────────────────
    if bins["passwords"] or bins["hashes"]:
        _section("Credentials leaked")
        if bins["passwords"]:
            _multirow(f"passwords {DIM}({len(bins['passwords'])}){RST}", [
                (v, ", ".join(b) if b else None) for v, b in bins["passwords"]
            ])
        if bins["hashes"]:
            if bins["passwords"]:
                print()
            _multirow(f"hashes {DIM}({len(bins['hashes'])}){RST}", [
                (v, ", ".join(b) if b else None) for v, b in bins["hashes"]
            ])

    # ── Activity ─────────────────────────────────
    activity_lines = [evt for evt, _src in bins["activity"]]
    if bins["dates"]:
        by_breach = {}
        for date_label, date_val, breach in bins["dates"]:
            norm = re.sub(r"\s*×\d+\s*$", "", date_label)
            norm = re.sub(r"\s*\+\d+\s*more\s*$", "", norm)
            if norm.lower().strip() == breach.lower().strip():
                by_breach.setdefault(breach, []).append(date_val)
            else:
                by_breach.setdefault(breach, []).append(f"{norm}: {date_val}")
        for breach in sorted(by_breach):
            for entry in by_breach[breach][:5]:
                activity_lines.append((entry, breach))
    if activity_lines:
        _section("Activity")
        for item in activity_lines:
            if isinstance(item, tuple):
                _row("", item[0], item[1])
            else:
                _row("", item)

    # ── Links ────────────────────────────────────
    if bins["links"]:
        _section("Links", count=len(bins["links"]))
        for label, url in bins["links"]:
            _row("", url, label)

    print()


def _section_pretty(title, rows):
    rows = [(l, v) for (l, v) in rows if v]
    if not rows:
        return
    print(f"▌ {title}")
    max_label = max(len(l) for l, _ in rows)
    for label, value in rows:
        pad = " " * (2 + max_label + 3)
        if isinstance(value, list):
            if not value:
                continue
            first, *rest = value
            print(f"  {label.ljust(max_label)} : {first}")
            for line in rest:
                print(f"{pad}{line}")
        else:
            print(f"  {label.ljust(max_label)} : {value}")
    print()


def _format_attributed(items):
    if not items:
        return None
    return [f"{value} ({attr})" for value, attr in items]


def _format_plain(items):
    if not items:
        return None
    return list(items)


def _format_creds(items):
    if not items:
        return None
    out = []
    for value, attr in items[:15]:
        out.append(f"{value}  [{attr}]")
    if len(items) > 15:
        out.append(f"+{len(items) - 15} more")
    return out


def _wrap(text, width):
    out, line = [], ""
    for chunk in text.split(", "):
        candidate = chunk if not line else f"{line}, {chunk}"
        if len(candidate) > width and line:
            out.append(line + ",")
            line = chunk
        else:
            line = candidate
    if line:
        out.append(line)
    return out


# Bin findings into identity sections. The classifier is permissive on
# purpose — modules emit slightly different shapes, and we'd rather fall
# back to "other" than mis-categorize.
def _bin_findings(results, target=None):
    target_local = _email_local(target)

    bins = {
        "names": [],            # [(name, [breaches], authoritative_src)]
        "aliases": [],          # [(value, [breaches])]
        "photos": [],
        "ids": [],
        "phones": [],           # [(value, [breaches])]
        "carriers": [],         # [(name, [breaches])]
        "ips": [],              # [(ip, [breaches])]
        "alt_emails": [],
        "locations": [],        # [(value, [breaches])]
        "registered_on": [],
        "passwords": [],        # [(value, [breaches])]
        "hashes": [],           # [(value, [breaches])]
        "breaches": [],
        "links": [],
        "activity": [],
        "dates": [],            # [(label, value, breach)]
        "other": [],
    }

    seen = set()

    def add(bucket, dedupe_key, payload):
        sig = (bucket, dedupe_key)
        if sig in seen:
            return
        seen.add(sig)
        bins[bucket].append(payload)

    # Mergers — collect breach attributions per unique value so we end
    # up with one row per value ("password X seen in [breach1, breach2]")
    # instead of one row per record.
    def _make_merger():
        return {}

    name_merge = _make_merger()
    alias_merge = _make_merger()
    phone_merge = _make_merger()
    carrier_merge = _make_merger()
    ip_merge = _make_merger()
    location_merge = _make_merger()
    password_merge = _make_merger()
    hash_merge = _make_merger()
    altemail_merge = _make_merger()

    def _merge_into(merger, value, breach):
        key = value.lower().strip()
        if not key:
            return
        slot = merger.setdefault(key, {"value": value, "breaches": []})
        if breach and breach not in slot["breaches"]:
            slot["breaches"].append(breach)

    def _explode_breaches(breach_attr):
        """Expand 'Foo ×3, Bar, +2 more' into ['Foo', 'Bar']."""
        if not breach_attr:
            return []
        out = []
        for chunk in breach_attr.split(","):
            chunk = chunk.strip()
            chunk = re.sub(r"\s*×\d+\s*$", "", chunk)
            chunk = re.sub(r"\s*\+\d+\s*more\s*$", "", chunk)
            if chunk and chunk.lower() not in ("unknown", "summary"):
                out.append(chunk)
        return out

    # Names from authoritative sources (GHunt, GitFive direct API) bypass
    # the cross-corroboration filter.
    authoritative_names = []  # [(name, source_label)]
    authoritative_aliases = []

    # Breaches need cross-source merging — Haxalot, 9Ghz, HIBP, IntelX
    # can all report the same breach name, and we want one row per breach
    # with attribution like "Exploit.In [Haxalot, 9Ghz, HIBP]".
    breach_merge: dict = {}

    def merge_breach(name, date, src):
        name = name.strip()
        if not name or name.lower() in {"unknown", "summary", ""}:
            return
        key = _normalize_breach_key(name)
        slot = breach_merge.setdefault(key, {
            "name": name,
            "date": "",
            "sources": [],
        })
        # Prefer the longer/more specific casing if multiple sources
        # disagree (e.g. "exploit.in" vs "Exploit.In").
        if name and (len(name) > len(slot["name"]) or
                      (name != slot["name"] and any(c.isupper() for c in name))):
            slot["name"] = name
        if date and not slot["date"]:
            slot["date"] = date
        if src and src not in slot["sources"]:
            slot["sources"].append(src)

    for r in results:
        source = r.get("source", "") or ""
        group = r.get("group") or ""
        label = str(r.get("label", "") or "")
        value = str(r.get("value", "") or "").strip()

        if not value:
            continue

        ll = label.lower()
        vl = value.lower()
        gl = group.lower()

        if ll == "more" or any(x in vl for x in (
            "more entries", "more breaches", "more unique values"
        )):
            continue
        if ll == "sources":
            continue

        if source == "GHunt":
            if label == "Name":
                authoritative_names.append((value, "Google"))
            elif label == "Gaia ID":
                add("ids", ("gaia", value), ("Google Gaia", value, "GHunt"))
            elif label == "Profile Photo":
                add("photos", value, (value, "Google"))
            elif label == "Active":
                add("activity", ("ghunt-active", value),
                    (f"Google: active in {value}", "GHunt"))
            elif "maps" in gl:
                if label == "Profile":
                    add("links", ("gmaps", value), ("Google Maps", value))
                elif value not in ("0", "None"):
                    add("activity", ("ghunt-maps-" + label, value),
                        (f"Google Maps {label.lower()}: {value}", "GHunt"))
            continue

        if source == "GitFive":
            if label == "Username":
                authoritative_aliases.append((value, "GitHub"))
            elif label == "Name":
                authoritative_names.append((value, "GitHub"))
            elif label == "ID":
                add("ids", ("github", value), ("GitHub", value, "GitFive"))
            elif label == "Email Resolved":
                add("activity", ("github-resolve", value),
                    (f"GitHub: {value}", "GitFive"))
            continue

        if source == "EmailEnum":
            if "registered" in vl:
                service = label or (group.split("/")[-1].strip() if "/" in group else group)
                add("registered_on", service.lower(), (service, "EmailEnum"))
            elif "rate limited" in vl:
                add("other", ("rl-" + label, value),
                    (label, "rate limited", "EmailEnum"))
            continue

        # Sources that report breach lists feed into the merger so the
        # final dossier shows one row per breach with merged attribution.
        if source in ("9Ghz", "HIBP") and label == "Breach":
            m = re.match(r"^(.*?)\s*\(([^)]+)\)\s*$", value)
            if m:
                merge_breach(m.group(1).strip(), m.group(2).strip(), source)
            else:
                merge_breach(value, "", source)
            continue

        # IntelX records identify "name (bucket, date)" — name is the
        # breach/leak label, bucket is the data store. Treat the name
        # like any other breach hit so cross-source dedup works.
        if source == "IntelX" and label.startswith("Result"):
            m = re.match(r"^(.*?)\s*\(([^,]+),\s*([^)]+)\)\s*$", value)
            if m:
                merge_breach(m.group(1).strip(), m.group(3).strip(), "IntelX")
            else:
                merge_breach(value, "", "IntelX")
            continue

        if source in ("9Ghz", "HIBP", "IntelX"):
            # Non-breach rows from these modules (counts, summaries) are
            # already represented by the merged breach list, so skip them.
            continue

        if source == "Haxalot":
            cat, breach_attr = _haxalot_classify(group, label)
            breach_chunks = _explode_breaches(breach_attr)
            for chunk in breach_chunks:
                merge_breach(chunk, "", "Haxalot")

            # Pick the first contributing breach as the "primary" attr
            # for value-level rows (used as the merger's per-breach key).
            primary_breach = breach_chunks[0] if breach_chunks else "Haxalot"

            if cat == "passwords":
                _merge_into(password_merge, value, primary_breach)
            elif cat == "hashes":
                # Filter obvious junk: very short tokens that aren't actual
                # hashes (e.g. salt fragments < 6 chars).
                if len(value) >= 6:
                    _merge_into(hash_merge, value, primary_breach)
            elif cat == "names":
                _merge_into(name_merge, value, primary_breach)
            elif cat == "aliases":
                _merge_into(alias_merge, value, primary_breach)
            elif cat == "phones":
                if _looks_like_carrier(value):
                    _merge_into(carrier_merge, value, primary_breach)
                elif _looks_like_phone_number(value):
                    _merge_into(phone_merge, value, primary_breach)
                # else: silently drop noise
            elif cat == "alt_emails":
                _merge_into(altemail_merge, value, primary_breach)
            elif cat == "locations":
                if _is_meaningful_location(value):
                    _merge_into(location_merge, value, primary_breach)
            elif cat == "ips":
                if _is_ip(value):
                    _merge_into(ip_merge, value, primary_breach)
            elif cat == "dates":
                bins["dates"].append((label, value, primary_breach))
            elif cat == "links":
                add("links", value, (primary_breach or "Haxalot", value))
            elif cat == "ids":
                add("ids", (label, value), (label, value, "Haxalot"))
            else:
                add("other", ("hax-" + label, value),
                    (label, value, f"Haxalot/{primary_breach}"))
            continue

        add("other", (source + label, value), (label, value, source))

    # Materialize merged breaches.
    for slot in sorted(
        breach_merge.values(),
        key=lambda s: (-len(s["sources"]), s["name"].lower()),
    ):
        bins["breaches"].append((
            slot["name"],
            slot["date"],
            ", ".join(slot["sources"]),
        ))

    # ---- Names: only keep cross-corroborated or target-matching ones.
    # Authoritative names from GHunt/GitFive go first, regardless of
    # breach support.
    auth_seen = set()
    for value, src in authoritative_names:
        key = value.lower()
        if key in auth_seen:
            continue
        auth_seen.add(key)
        bins["names"].append((value, [], src))

    for slot in name_merge.values():
        if slot["value"].lower() in auth_seen:
            continue
        v = slot["value"]
        if len(v) > 40:
            continue
        # Names that contain digits are almost always handles/usernames
        # disguised as a Name field (e.g. "f666ck", "Clarissa_03"). Route
        # them to aliases instead of dropping them outright.
        if re.search(r"\d", v) or re.search(r"[._-]", v):
            alias_merge.setdefault(v.lower(), {
                "value": v, "breaches": []
            })["breaches"].extend(
                b for b in slot["breaches"]
                if b not in alias_merge[v.lower()]["breaches"]
            )
            continue
        # Cross-corroborated (>= 2 distinct breaches) OR matches target email.
        is_corroborated = len(slot["breaches"]) >= 2
        is_target_match = _name_matches_target(v, target_local)
        if is_corroborated or is_target_match:
            bins["names"].append((v, sorted(slot["breaches"]), None))

    # Sort: target-match first, then by breach count desc, then alpha.
    bins["names"].sort(key=lambda t: (
        0 if t[2] else (1 if _name_matches_target(t[0], target_local) else 2),
        -len(t[1]),
        t[0].lower(),
    ))

    # ---- Aliases: include all non-empty, sort by breach count.
    auth_alias_seen = set()
    for value, src in authoritative_aliases:
        key = value.lower()
        if key in auth_alias_seen:
            continue
        auth_alias_seen.add(key)
        bins["aliases"].append((value, [src]))

    for slot in alias_merge.values():
        if slot["value"].lower() in auth_alias_seen:
            continue
        bins["aliases"].append((slot["value"], sorted(slot["breaches"])))

    bins["aliases"].sort(key=lambda t: (-len(t[1]), t[0].lower()))

    # ---- Other mergers: just materialize.
    for slot in sorted(phone_merge.values(),
                        key=lambda s: (-len(s["breaches"]), s["value"])):
        bins["phones"].append((slot["value"], sorted(slot["breaches"])))

    for slot in sorted(carrier_merge.values(),
                        key=lambda s: (-len(s["breaches"]), s["value"].lower())):
        bins["carriers"].append((slot["value"], sorted(slot["breaches"])))

    for slot in sorted(ip_merge.values(),
                        key=lambda s: (-len(s["breaches"]), s["value"])):
        bins["ips"].append((slot["value"], sorted(slot["breaches"])))

    for slot in sorted(location_merge.values(),
                        key=lambda s: (-len(s["breaches"]), s["value"].lower())):
        bins["locations"].append((slot["value"], sorted(slot["breaches"])))

    for slot in sorted(altemail_merge.values(),
                        key=lambda s: (-len(s["breaches"]), s["value"].lower())):
        bins["alt_emails"].append((slot["value"], sorted(slot["breaches"])))

    for slot in sorted(password_merge.values(),
                        key=lambda s: (-len(s["breaches"]), s["value"].lower())):
        bins["passwords"].append((slot["value"], sorted(slot["breaches"])))

    for slot in sorted(hash_merge.values(),
                        key=lambda s: (-len(s["breaches"]), s["value"].lower())):
        bins["hashes"].append((slot["value"], sorted(slot["breaches"])))

    return bins


def _normalize_breach_key(name: str) -> str:
    """Best-effort normalization for cross-source breach matching.

    Strips trailing version markers, "database"/"dump" suffixes, year
    suffixes, and casing so 9Ghz's "Exploit.In Database (2017)" merges
    with HIBP's "exploit.in" and Haxalot's "Exploit.In".
    """
    s = name.strip().lower()
    # Drop trailing parenthetical (years, sizes, "Breach", etc.)
    s = re.sub(r"\s*\([^)]*\)\s*$", "", s)
    # Drop common suffixes that vary across sources.
    s = re.sub(r"\s+(database|dump|leak|breach|scrape|combolist|combo|dbs?)\s*$", "", s)
    s = re.sub(r"\s+\d{4}\s*$", "", s)  # Trailing year
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _haxalot_classify(group, label):
    """Map a Haxalot row to (category, breach_attribution).

    Handles both the new aggregated format (data type in `group`, breach
    list in `label`) and the legacy per-breach format (breach in `group`,
    field name in `label`).
    """
    new_format = {
        "🔑 passwords": "passwords",
        "🔐 hashes": "hashes",
        "👤 names": "names",
        "👥 aliases": "aliases",
        "📍 locations": "locations",
        "📱 phones": "phones",
        "📧 emails": "alt_emails",
        "🌐 ips": "ips",
        "💻 devices": "other",
        "🔗 links": "links",
        "💸 financial": "other",
        "🏢 companies": "other",
        "🆔 identifiers": "ids",
        "📆 dates": "dates",
        "📝 content": "other",
        "📋 other": "other",
        "📋 summary": "summary",
    }
    gl = group.lower().strip()
    if gl in new_format:
        return new_format[gl], (label or "Unknown").strip()

    breach = (group or "Unknown").strip()
    field = re.sub(r"^[^\w]+", "", label).strip().lower()

    if "password" in field and "encrypted" in field:
        return "hashes", breach
    if "password" in field:
        return "passwords", breach
    if "hash" in field or "salt" in field:
        return "hashes", breach
    if field == "ip" or "ip address" in field:
        return "ips", breach
    if "phone" in field or "mobile operator" in field:
        return "phones", breach
    if "email" in field:
        return "alt_emails", breach
    if "nick" in field:
        return "aliases", breach
    if "name" in field or "surname" in field:
        return "names", breach
    if any(k in field for k in ("address", "adres", "city", "region", "country",
                                "state ", "postal", "pin code", "zip",
                                "latitude", "longitude")) or field.strip() == "state":
        return "locations", breach
    if "date" in field or "activity" in field or "registration" in field:
        return "dates", breach
    if any(k in field for k in ("link", "website", "url", "app (")):
        return "links", breach
    if field.endswith("id") or " id" in field:
        return "ids", breach
    return "other", breach
