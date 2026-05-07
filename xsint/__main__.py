import argparse
import asyncio
import contextlib
import getpass
import importlib
import io
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

from . import __version__
from ._version_check import check_for_update
from .config import get_config
from .core import XsintEngine
from .ui import print_results


API_KEY_SERVICES = {"hibp", "intelx", "9ghz"}
LOGIN_SERVICES = {"ghunt", "gitfive"}
SETUP_SERVICES = {"haxalot"}
ALL_AUTH_SERVICES = API_KEY_SERVICES | LOGIN_SERVICES | SETUP_SERVICES
CUSTOM_MODULES = {"instagram", "phone_basic", "email_enum", "phone_enum"}


def _normalize_service(service):
    s = service.strip().lower()
    return "9ghz" if s in {"nineghz", "9ghz"} else s


def _validate_proxy(url):
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        raise ValueError(f"invalid proxy URL: {url}")
    if ":" in parsed.netloc:
        _, port = parsed.netloc.rsplit(":", 1)
        try:
            p = int(port)
        except ValueError:
            raise ValueError(f"invalid proxy port: {port}")
        if not 1 <= p <= 65535:
            raise ValueError(f"proxy port out of range: {p}")


def _proxy_reachable(url, timeout=2.0):
    """Quick TCP probe of the proxy's host:port. Returns True if reachable."""
    import socket
    parsed = urlparse(url)
    host = parsed.hostname
    port = parsed.port
    if port is None:
        # Default ports for the schemes we care about.
        port = {"http": 80, "https": 443, "socks4": 1080, "socks5": 1080}.get(parsed.scheme, 80)
    if not host:
        return False
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False


def _run_external_login(service):
    service = _normalize_service(service)
    candidates = []

    # 1. Binary on PATH (most reliable for pipx-installed CLI tools).
    which_path = shutil.which(service)
    if which_path:
        candidates.append([which_path, "login"])

    # 2. Default pipx venv binary.
    candidates.append([
        os.path.expanduser(f"~/.local/pipx/venvs/{service}/bin/{service}"),
        "login",
    ])

    # 3. Binary alongside the active interpreter (venv-aware).
    candidates.append([
        os.path.join(os.path.dirname(sys.executable), service),
        "login",
    ])

    # 4. python -m fallback. ghunt's package has no __main__ so we skip it
    #    here; gitfive needs to call the parser directly because the
    #    installed CLI script lives outside the package.
    if service == "gitfive":
        candidates.append([
            sys.executable, "-c",
            "from gitfive.lib.cli import parse_args; parse_args()", "login",
        ])
    elif service != "ghunt":
        candidates.append([sys.executable, "-m", service, "login"])

    attempted = False
    for cmd in candidates:
        exe = cmd[0]
        if os.path.sep in exe and not (os.path.isfile(exe) and os.access(exe, os.X_OK)):
            continue
        try:
            attempted = True
            if subprocess.run(cmd).returncode == 0:
                return True, True
            # Non-zero — try the next candidate rather than bailing. Many
            # services have a 'wrong way to invoke me' error path (e.g.
            # python -m ghunt) that exits 1 even though another candidate
            # would succeed.
        except Exception:
            continue
    return False, attempted


def _print_auth_status():
    config = get_config()
    api_auth_types = {"9ghz": "api_key", "hibp": "api_key", "intelx": "api_key"}

    rows = []
    for service in sorted(api_auth_types):
        env_key = os.environ.get(f"XSINT_{service.upper()}_API_KEY", "").strip()
        cfg_key = (config.get(f"{service}_key", "") or "").strip()
        if env_key:
            rows.append((service, api_auth_types[service], "set", "env", "-"))
        elif cfg_key:
            rows.append((service, api_auth_types[service], "set", "config", "-"))
        else:
            rows.append((service, api_auth_types[service], "missing", "-", f"xsint --auth {service} <value>"))

    runtime = [
        ("ghunt", "login", "ghunt_lookup", "xsint --auth ghunt"),
        ("gitfive", "login", "gitfive_module", "xsint --auth gitfive"),
        ("haxalot", "setup(optional)", "haxalot_module", "xsint --auth haxalot"),
    ]
    for service, auth_type, module_name, hint in runtime:
        status, source, h = "missing", "-", hint
        try:
            mod = importlib.import_module(f"xsint.modules.{module_name}")
            checker = getattr(mod, "is_ready", None)
            if callable(checker):
                result = checker()
                if isinstance(result, tuple):
                    ready = bool(result[0])
                    reason = str(result[1]) if len(result) > 1 and result[1] else ""
                else:
                    ready, reason = bool(result), ""
                if ready:
                    status, source, h = "set", "session", "-"
                elif reason == "not installed":
                    status, source, h = "not installed", "-", "install dependency"
                elif reason and reason != hint:
                    h = reason
            else:
                status, source, h = "set", "-", "-"
        except Exception:
            status, source, h = "not installed", "-", "install dependency"
        rows.append((service, auth_type, status, source, h))

    headers = ("module", "auth", "status", "source", "hint")
    _print_table(headers, rows)


_GREEN = "\033[32m"
_RED = "\033[31m"
_YELLOW = "\033[33m"
_RESET = "\033[0m"


def _module_status_line(name, info, stream):
    """Format one dashboard line for `name`, colored if `stream` is a TTY.

    [*] yellow → still running
    [+] green  → finished, results > 0
    [-] red    → finished, no results
    """
    is_tty = stream.isatty()

    def paint(text, color):
        return f"{color}{text}{_RESET}" if is_tty else text

    if info["status"] == "running":
        # Each module gets a phase offset hashed from its name so their
        # dot animations don't tick in unison — gives the impression of
        # independent per-module pacing without per-module timers.
        DOT_FRAMES = [".  ", ".. ", "...", " ..", "  .", "   "]
        offset = (abs(hash(name)) // 7) % len(DOT_FRAMES)
        phase = (int(time.monotonic() * 4) + offset) % len(DOT_FRAMES)
        return f"{paint('[*]', _YELLOW)} {name}: {DOT_FRAMES[phase]}"

    n = info["count"]
    if n > 0:
        suffix = "s" if n != 1 else ""
        return f"{paint('[+]', _GREEN)} {name}: {n} result{suffix}"
    return f"{paint('[-]', _RED)} {name}: no results"


def _colorize_status(value):
    if not sys.stdout.isatty():
        return value
    if value == "active":
        return f"{_GREEN}{value}{_RESET}"
    if value == "locked":
        return f"{_RED}{value}{_RESET}"
    return value


def _print_table(headers, rows):
    # Compute widths from raw values (no ANSI codes) so columns align.
    cols = list(zip(headers, *rows)) if rows else [(h,) for h in headers]
    widths = [max(len(str(c)) for c in col) for col in cols]
    status_idx = headers.index("status") if "status" in headers else -1
    print("  ".join(str(h).ljust(w) for h, w in zip(headers, widths)))
    for row in rows:
        out = []
        for i, (cell, w) in enumerate(zip(row, widths)):
            text = str(cell)
            pad = " " * (w - len(text))
            if i == status_idx:
                out.append(_colorize_status(text) + pad)
            else:
                out.append(text + pad)
        print("  ".join(out))


def _build_modules_table(caps, type_filter="all"):
    selected = sorted(caps) if type_filter == "all" else [type_filter]
    by_module = {}
    for type_name in selected:
        for mod in caps.get(type_name, []):
            entry = by_module.setdefault(mod["name"], {"statuses": set(), "types": []})
            entry["statuses"].add(mod["status"])
            if type_name.upper() not in entry["types"]:
                entry["types"].append(type_name.upper())

    def source_for(name):
        return "custom" if name in CUSTOM_MODULES else "external"

    rows = []
    for name in sorted(by_module, key=lambda n: (0 if source_for(n) == "custom" else 1, n)):
        entry = by_module[name]
        status = "active" if "active" in entry["statuses"] else "locked"
        rows.append((name, source_for(name), status, "|".join(entry["types"]) or "-"))
    return rows


HELP_TEXT = f"""\
xsint {__version__} ( https://github.com/h1lw/xsint )
Usage: xsint [Options] {{target}}

TARGET SPECIFICATION:
  Auto-detected types: email, username, phone, ip, address, hash, name, id, ssn, passport
  Use a prefix to disambiguate: user:admin, addr:"Tokyo, Japan", hash:5f4dcc3b
  Ex: xsint user@example.com; xsint ip:8.8.8.8; xsint phone:+14155551234

MODULE LISTING:
  -m, --modules [TYPE]: List modules; optionally filter by input type (e.g. -m email)

AUTHENTICATION:
  --auth: Show credential status for all auth-gated modules
  --auth <service> <key>: Save API key (hibp, intelx, 9ghz)
  --auth <service>: Run interactive setup (ghunt, gitfive, haxalot)

NETWORK:
  --proxy <URL>: Proxy URL for this run (http://, socks5://, ...)
                 Set XSINT_PROXY in the environment to persist.

OUTPUT FORMAT (mutually exclusive; default --pretty):
  --pretty      : Synthesized identity dossier (default) — deduped person summary
  --raw         : Plain text dump grouped by source
  --json        : Full report as JSON (pipe to a file or another tool)
  --html <PATH> : Self-contained HTML report written to PATH

MISC:
  -V, --version: Print xsint version and exit
  -U, --update : Pull the latest xsint from GitHub and reinstall in place
      --no-version-check: Skip the GitHub update check for this run
  -h, --help: Print this help summary
"""


class _XsintParser(argparse.ArgumentParser):
    def format_help(self):
        return HELP_TEXT

    def format_usage(self):
        return "Usage: xsint [Options] {target}\n"


_INSTALL_URL = "https://raw.githubusercontent.com/h1lw/xsint/main/install.sh"


def _maybe_print_update_notice():
    """Print a one-line update prompt if a newer version is on GitHub."""
    try:
        info = check_for_update()
    except Exception:
        return
    if not info:
        return
    cur, latest = info
    if sys.stdout.isatty():
        print(f"\033[33m[!] xsint {latest} is available (you have {cur}).\033[0m", file=sys.stderr)
        print(f"\033[2m    Update with: xsint --update\033[0m", file=sys.stderr)
    else:
        print(f"[!] xsint {latest} is available (you have {cur}).", file=sys.stderr)
        print("    Update with: xsint --update", file=sys.stderr)


def _do_update():
    """Re-run the install.sh from GitHub against the current install.

    Same script the curl one-liner uses; pulls the latest release,
    overwrites the install dir, regenerates the wrapper. Exits with the
    installer's return code.
    """
    if not shutil.which("bash"):
        print("[!] --update needs bash on PATH; install bash or run install.sh manually",
              file=sys.stderr)
        sys.exit(1)
    if not shutil.which("curl"):
        print("[!] --update needs curl on PATH; install curl or run install.sh manually",
              file=sys.stderr)
        sys.exit(1)

    print(f"[*] updating xsint from {_INSTALL_URL}", file=sys.stderr)
    print("    (this will overwrite the current install)", file=sys.stderr)
    cmd = f"curl -fsSL {_INSTALL_URL} | bash"
    rc = subprocess.call(cmd, shell=True)
    sys.exit(rc)


def _write_html_report(report, target, path_str):
    """Render the HTML report and write it to disk.

    `print_results(fmt="html")` writes the markup to stdout; we capture
    that here so the user gets a real file (`xsint --html report.html`)
    instead of having to pipe it themselves.
    """
    path = Path(path_str).expanduser()
    if path.parent and not path.parent.exists():
        path.parent.mkdir(parents=True, exist_ok=True)

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        print_results(report, target=target, fmt="html")
    path.write_text(buf.getvalue(), encoding="utf-8")
    print(f"[+] html report written to {path}", file=sys.stderr)


def main():
    parser = _XsintParser(prog="xsint", add_help=True)
    parser.add_argument("target", nargs="?")
    parser.add_argument("-m", "--modules", nargs="?", const="all", metavar="TYPE")
    parser.add_argument("--auth", nargs="*", metavar="ARGS")
    parser.add_argument("--proxy", metavar="URL")
    parser.add_argument("-V", "--version", action="store_true")
    parser.add_argument("-U", "--update", action="store_true")
    parser.add_argument("--no-version-check", action="store_true")

    fmt_group = parser.add_mutually_exclusive_group()
    fmt_group.add_argument("--raw", action="store_true")
    fmt_group.add_argument("--pretty", action="store_true")
    fmt_group.add_argument("--json", action="store_true")
    # --html requires a path: HTML reports are self-contained pages, not
    # something you'd want dumped into a terminal. Force the user to name
    # an output file so they get a usable artifact instead of a wall of
    # markup on stdout.
    fmt_group.add_argument("--html", metavar="PATH", default=None)

    if len(sys.argv) == 1:
        print(HELP_TEXT, end="")
        _maybe_print_update_notice()
        return

    args = parser.parse_args()

    # Derive output format from the mutex group flags. Mutex enforcement
    # means at most one of these is set; argparse already errored out if
    # the user passed two. Default is --pretty (the synthesized dossier);
    # --raw gives the legacy source-grouped dump for tooling that parses
    # it.
    if args.html is not None:
        args.fmt = "html"
    elif args.json:
        args.fmt = "json"
    elif args.raw:
        args.fmt = "raw"
    else:
        args.fmt = "pretty"

    if args.version:
        print(f"xsint {__version__}")
        return

    if args.update:
        # Skip the version-check spam — we're about to overwrite the
        # whole install anyway.
        _do_update()
        return

    if not args.no_version_check:
        _maybe_print_update_notice()

    if args.proxy:
        try:
            _validate_proxy(args.proxy)
        except ValueError as e:
            print(f"[!] {e}", file=sys.stderr)
            sys.exit(1)
        if not _proxy_reachable(args.proxy):
            print(f"[!] proxy unreachable: {args.proxy}", file=sys.stderr)
            sys.exit(1)

    if args.auth is not None:
        return _handle_auth(args.auth)

    try:
        asyncio.run(async_main(args))
    except KeyboardInterrupt:
        print("\n[!] interrupted", file=sys.stderr)
        sys.exit(1)


def _handle_auth(auth_args):
    if not auth_args:
        _print_auth_status()
        return

    service = _normalize_service(auth_args[0])

    if service in API_KEY_SERVICES:
        config = get_config()
        if len(auth_args) >= 2:
            key = " ".join(auth_args[1:]).strip()
        else:
            key = getpass.getpass("Credential value: ").strip()
        if not key:
            print("[!] no credential provided", file=sys.stderr)
            return
        config.set(f"{service}_key", key)
        print(f"saved: {service}")
        return

    if service in LOGIN_SERVICES:
        ok, attempted = _run_external_login(service)
        if not ok:
            if attempted:
                print(f"[!] {service} login did not complete. retry: xsint --auth {service}", file=sys.stderr)
            else:
                print(f"[!] {service} not found. install {service} and run '{service} login'", file=sys.stderr)
        return

    if service in SETUP_SERVICES:
        try:
            from .modules import haxalot_module
            asyncio.run(haxalot_module.setup())
        except ModuleNotFoundError as e:
            print(f"[!] haxalot setup unavailable: missing '{getattr(e, 'name', 'dependency')}'", file=sys.stderr)
        except KeyboardInterrupt:
            print("\n[!] aborted", file=sys.stderr)
        except Exception as e:
            print(f"[!] setup failed: {e}", file=sys.stderr)
        return

    print(f"[!] unknown module: {service}", file=sys.stderr)
    print(f"    supported: {', '.join(sorted(ALL_AUTH_SERVICES))}", file=sys.stderr)


async def async_main(args):
    proxy = args.proxy or get_config().get("proxy")
    if proxy:
        get_config().data["proxy"] = proxy
        # Make every httpx client created by any module pick up the proxy
        # automatically via trust_env=True (httpx default). aiohttp clients
        # in the engine already wire proxy explicitly via ProxyConnector.
        for var in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY"):
            os.environ[var] = proxy
        # Intercept proxies (Burp, mitmproxy) present a self-signed CA. Default
        # every httpx.AsyncClient to verify=False so SSL errors don't kill
        # third-party modules that don't expose a verify kwarg of their own.
        import httpx as _httpx
        _orig_init = _httpx.AsyncClient.__init__
        if not getattr(_httpx.AsyncClient, "_xsint_verify_patched", False):
            def _patched_init(self, *a, **kw):
                kw.setdefault("verify", False)
                return _orig_init(self, *a, **kw)
            _httpx.AsyncClient.__init__ = _patched_init
            _httpx.AsyncClient._xsint_verify_patched = True

    engine = XsintEngine(proxy=proxy)
    try:
        if args.modules:
            caps = engine.get_capabilities()
            type_filter = args.modules.lower()
            if type_filter == "all" or type_filter in caps:
                rows = _build_modules_table(caps, type_filter)
                _print_table(("module", "source", "status", "types"), rows)
            else:
                print(f"[!] unknown type '{type_filter}'. available: {', '.join(sorted(caps))}", file=sys.stderr)
            return

        if not args.target:
            print(HELP_TEXT, end="")
            return

        ran_any = False
        # Where progress goes: machine-readable formats (--json, --html)
        # would corrupt stdout, so route the dashboard to stderr instead.
        # The animation still runs as long as the chosen stream is a TTY.
        to_stderr = args.fmt in ("json", "html")
        progress_stream = sys.stderr if to_stderr else sys.stdout
        animate = progress_stream.isatty()
        # name -> {status: "running"|"done", count: int, status_str: str}
        modules_state = {}
        spinner_stop = asyncio.Event()
        last_lines = [0]  # mutable so closures can update

        def _render():
            """Redraw the dashboard on the chosen progress stream."""
            lines = [
                _module_status_line(name, info, progress_stream)
                for name, info in modules_state.items()
            ]

            buf = []
            if last_lines[0]:
                buf.append(f"\033[{last_lines[0]}A")
            for rendered in lines:
                buf.append("\r\033[2K" + rendered + "\n")
            progress_stream.write("".join(buf))
            progress_stream.flush()
            last_lines[0] = len(lines)

        def on_progress(event):
            nonlocal ran_any
            kind = event.get("event")
            name = event.get("module", "?")
            if kind == "module_start":
                modules_state[name] = {"status": "running", "count": 0}
                if animate:
                    _render()
                else:
                    progress_stream.write(
                        _module_status_line(name, modules_state[name],
                                            progress_stream) + "\n"
                    )
                    progress_stream.flush()
            elif kind == "module_done":
                ran_any = True
                count = int(event.get("count", 0) or 0)
                modules_state[name] = {"status": "done", "count": count}
                if animate:
                    _render()
                else:
                    progress_stream.write(
                        _module_status_line(name, modules_state[name],
                                            progress_stream) + "\n"
                    )
                    progress_stream.flush()

        async def _animator():
            # Tick at ~12 fps. Faster than strictly needed for the 4 fps
            # dot animation, but more frequent ticks mean any one-off
            # event-loop hiccup (cold-cache import, lock contention)
            # doesn't stretch into a visible stutter.
            while not spinner_stop.is_set():
                if any(info["status"] == "running" for info in modules_state.values()):
                    _render()
                try:
                    await asyncio.wait_for(spinner_stop.wait(), timeout=0.08)
                except asyncio.TimeoutError:
                    pass

        spinner_task = asyncio.create_task(_animator()) if animate else None
        try:
            report = await engine.scan(args.target, progress_cb=on_progress)
        finally:
            spinner_stop.set()
            if spinner_task:
                await spinner_task
            # Final render so any module that wrapped up between the last
            # animator tick and the scan return is shown in its done state.
            if animate and modules_state:
                _render()

        if report.get("error"):
            print(f"[!] {report['error'].splitlines()[0]}", file=sys.stderr)
            return

        if not ran_any:
            print("[!] no eligible modules — run --auth to enable more, or check `xsint -m`",
                  file=sys.stderr)
            return

        # JSON/HTML still want a structured "empty" payload, so they
        # always render. Raw/pretty short-circuit on no results.
        empty = not (report.get("results") or [])
        if empty and args.fmt in ("raw", "pretty"):
            print("[!] no intel found", file=sys.stderr)
            return

        if args.fmt == "html":
            _write_html_report(report, args.target, args.html)
        else:
            if args.fmt == "raw" and not empty:
                print()
            print_results(report, target=args.target, fmt=args.fmt)
    finally:
        await engine.close()


if __name__ == "__main__":
    main()
