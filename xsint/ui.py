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
        bins = _bin_findings(results)

        # PERSON
        person_rows = []
        if bins["names"]:
            person_rows.append(("name", _html_attributed_list(bins["names"])))
        if bins["aliases"]:
            person_rows.append(("alias", _html_attributed_list(bins["aliases"])))
        if bins["photos"]:
            person_rows.append((
                "photo",
                _html_list([
                    f'<a href="{_html.escape(v)}" target="_blank" rel="noopener">'
                    f'{_html.escape(v)}</a>'
                    for v, _ in bins["photos"]
                ]),
            ))
        if person_rows:
            parts.append(_html_section("Person", person_rows))

        # ACCOUNTS
        account_rows = []
        for kind, value, src in bins["ids"]:
            account_rows.append((
                kind.lower(),
                f'<span class="mono">{_html.escape(str(value))}</span>'
                f' <span class="attr">({_html.escape(src)})</span>',
            ))
        if bins["registered_on"]:
            services = sorted({s for s, _ in bins["registered_on"]}, key=str.lower)
            tags = "".join(
                f'<span class="tag">{_html.escape(s)}</span>' for s in services
            )
            account_rows.append((f"registered ({len(services)})", tags))
        if account_rows:
            parts.append(_html_section("Accounts", account_rows))

        # CONTACT
        contact_rows = []
        if bins["phones"]:
            contact_rows.append(("phones", _html_attributed_list(bins["phones"])))
        if bins["alt_emails"]:
            contact_rows.append(("emails", _html_attributed_list(bins["alt_emails"])))
        if contact_rows:
            parts.append(_html_section("Contact", contact_rows))

        # LOCATIONS
        if bins["locations"]:
            parts.append(_html_section("Locations", [
                ("seen", _html_attributed_list(bins["locations"]))
            ]))

        # BREACH EXPOSURE
        if bins["breaches"]:
            tags = "".join(
                f'<span class="tag breach-tag">'
                f'{_html.escape(name)}'
                f'{(" — " + _html.escape(date)) if date else ""}'
                f' <span class="attr">[{_html.escape(src)}]</span>'
                f'</span>'
                for name, date, src in bins["breaches"]
            )
            parts.append(_html_section("Breach exposure", [
                ("count", str(len(bins["breaches"]))),
                ("breaches", tags),
            ]))

        # CREDENTIALS LEAKED
        cred_rows = []
        if bins["passwords"]:
            cred_rows.append(("passwords",
                _html_list([
                    f'<span class="secret">{_html.escape(v)}</span>'
                    f' <span class="attr">[{_html.escape(attr)}]</span>'
                    for v, attr in bins["passwords"]
                ])
            ))
        if bins["hashes"]:
            cred_rows.append(("hashes",
                _html_list([
                    f'<span class="hash">{_html.escape(v)}</span>'
                    f' <span class="attr">[{_html.escape(attr)}]</span>'
                    for v, attr in bins["hashes"]
                ])
            ))
        if cred_rows:
            parts.append(_html_section("Credentials leaked", cred_rows))

        # ACTIVITY
        if bins["activity"]:
            parts.append(_html_section("Activity", [
                ("events",
                 _html_list([_html.escape(label) for label, _src in bins["activity"]]))
            ]))

        # LINKS
        if bins["links"]:
            parts.append(_html_section("Links", [
                ("seen",
                 _html_list([
                     f'<span class="attr">{_html.escape(label)}:</span> '
                     f'<a href="{_html.escape(url)}" target="_blank" rel="noopener">'
                     f'{_html.escape(url)}</a>'
                     for label, url in bins["links"]
                 ]))
            ]))

        # OTHER (anything we couldn't classify) — fold in last so nothing
        # silently disappears.
        if bins["other"]:
            parts.append(_html_section("Other", [
                ("misc",
                 _html_list([
                     f'<span class="attr">{_html.escape(str(a))}:</span> '
                     f'{_linkify_html(str(b))} '
                     f'<span class="attr">({_html.escape(str(c))})</span>'
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


def _linkify_html(text):
    escaped = _html.escape(text)
    return re.sub(
        r"(https?://[^\s)>\"]+)",
        lambda m: f'<a href="{m.group(1)}" rel="noopener noreferrer" target="_blank">{m.group(1)}</a>',
        escaped,
    )


# ---------- pretty (identity dossier) ----------

def _print_pretty(report, target):
    target_type = str(report.get("type", "unknown")).upper()
    error = report.get("error")

    width = 64
    line = "=" * width
    sep = "-" * width

    print(line)
    print("  IDENTITY REPORT")
    print(line)
    print(f"  target   : {target or '(unknown)'}")
    print(f"  type     : {target_type}")
    print(f"  scanned  : {time.strftime('%Y-%m-%d %H:%M', time.localtime())}")

    if error:
        print(f"  status   : aborted")
        print(f"  error    : {error}")
        print(line)
        return

    results = report.get("results", []) or []
    sources = sorted({r.get("source") for r in results if r.get("source")})
    print(f"  findings : {len(results)} across {len(sources)} sources")
    print(sep)
    print()

    if not results:
        print("  no intel found")
        print(line)
        return

    bins = _bin_findings(results)

    _section_pretty("PERSON", [
        ("name", _format_attributed(bins["names"])),
        ("alias", _format_attributed(bins["aliases"])),
        ("photo", _format_plain([v for v, _ in bins["photos"]])),
    ])

    account_rows = []
    for kind, value, src in bins["ids"]:
        account_rows.append((kind.lower(), f"{value} ({src})"))
    if bins["registered_on"]:
        services = sorted({s for s, _ in bins["registered_on"]}, key=str.lower)
        account_rows.append(("registered on", _wrap(", ".join(services), 56)))
    _section_pretty("ACCOUNTS", account_rows)

    _section_pretty("CONTACT", [
        ("phones", _format_attributed(bins["phones"])),
        ("emails", _format_attributed(bins["alt_emails"])),
    ])

    if bins["locations"]:
        _section_pretty("LOCATIONS", [
            ("seen", _format_attributed(bins["locations"]))
        ])

    if bins["breaches"]:
        breach_lines = []
        for name, date, src in bins["breaches"]:
            tail = f" ({date})" if date else ""
            breach_lines.append(f"{name}{tail} [{src}]")
        _section_pretty("BREACH EXPOSURE", [
            ("count", str(len(bins["breaches"]))),
            ("breaches", breach_lines),
        ])

    cred_rows = []
    if bins["passwords"]:
        cred_rows.append(("passwords", _format_creds(bins["passwords"])))
    if bins["hashes"]:
        cred_rows.append(("hashes", _format_creds(bins["hashes"])))
    if cred_rows:
        _section_pretty("CREDENTIALS LEAKED", cred_rows)

    if bins["activity"]:
        _section_pretty("ACTIVITY", [
            ("events", [label for label, _src in bins["activity"][:12]])
        ])

    if bins["links"]:
        link_lines = [f"{label}: {url}" for label, url in bins["links"][:10]]
        _section_pretty("LINKS", [("seen", link_lines)])

    print(sep)


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
def _bin_findings(results):
    bins = {
        "names": [],
        "aliases": [],
        "photos": [],
        "ids": [],
        "phones": [],
        "alt_emails": [],
        "locations": [],
        "registered_on": [],
        "passwords": [],
        "hashes": [],
        "breaches": [],
        "links": [],
        "activity": [],
        "other": [],
    }

    seen = set()

    def add(bucket, dedupe_key, payload):
        sig = (bucket, dedupe_key)
        if sig in seen:
            return
        seen.add(sig)
        bins[bucket].append(payload)

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
                add("names", value.lower(), (value, "Google"))
            elif label == "Gaia ID":
                add("ids", ("gaia", value), ("Google Gaia", value, "GHunt"))
            elif label == "Profile Photo":
                add("photos", value, (value, "Google"))
            elif label == "Active":
                add("activity", ("ghunt-active", value),
                    (f"Google: active in {value}", "GHunt"))
            elif "maps" in gl:
                if label == "Profile":
                    add("links", ("gmaps", value), ("google maps", value))
                elif value not in ("0", "None"):
                    add("activity", ("ghunt-maps-" + label, value),
                        (f"Google Maps {label.lower()}: {value}", "GHunt"))
            continue

        if source == "GitFive":
            if label == "Username":
                add("aliases", value.lower(), (value, "GitHub"))
            elif label == "Name":
                add("names", value.lower(), (value, "GitHub"))
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
                    (f"{label}: rate limited", "EmailEnum"))
            continue

        if source == "9Ghz":
            if label == "Breach":
                m = re.match(r"^(.*?)\s*\(([^)]+)\)\s*$", value)
                if m:
                    add("breaches", m.group(1).strip().lower(),
                        (m.group(1).strip(), m.group(2).strip(), "9Ghz"))
                else:
                    add("breaches", value.lower(), (value, "", "9Ghz"))
            continue

        if source == "Haxalot":
            cat, breach_attr = _haxalot_classify(group, label)
            if breach_attr and breach_attr.lower() not in ("unknown", "summary"):
                first = breach_attr.split(",")[0].strip()
                first = re.sub(r"\s*×\d+\s*$", "", first)
                first = re.sub(r"\s*\+\d+\s*more\s*$", "", first)
                if first:
                    add("breaches", first.lower(), (first, "", "Haxalot"))

            if cat == "passwords":
                add("passwords", value, (value, breach_attr))
            elif cat == "hashes":
                add("hashes", value, (value, breach_attr))
            elif cat == "names":
                add("names", value.lower(), (value, f"Haxalot/{breach_attr}"))
            elif cat == "aliases":
                add("aliases", value.lower(), (value, f"Haxalot/{breach_attr}"))
            elif cat == "phones":
                add("phones", value, (value, f"Haxalot/{breach_attr}"))
            elif cat == "alt_emails":
                add("alt_emails", value.lower(), (value, f"Haxalot/{breach_attr}"))
            elif cat == "locations":
                add("locations", value.lower(), (value, f"Haxalot/{breach_attr}"))
            elif cat == "ips":
                add("activity", ("hax-ip", value),
                    (f"IP {value} ({breach_attr})", "Haxalot"))
            elif cat == "dates":
                add("activity", ("hax-date-" + label, value),
                    (f"{label}: {value} ({breach_attr})", "Haxalot"))
            elif cat == "links":
                add("links", value, (f"haxalot/{breach_attr}", value))
            elif cat == "ids":
                add("ids", (label, value), (label, value, "Haxalot"))
            else:
                add("other", ("hax-" + label, value),
                    (f"{label}: {value}", f"Haxalot/{breach_attr}"))
            continue

        add("other", (source + label, value), (label, value, source))

    return bins


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
                                "stat", "postal", "pin code", "zip",
                                "latitude", "longitude")):
        return "locations", breach
    if "date" in field or "activity" in field or "registration" in field:
        return "dates", breach
    if any(k in field for k in ("link", "website", "url", "app (")):
        return "links", breach
    if field.endswith("id") or " id" in field:
        return "ids", breach
    return "other", breach
