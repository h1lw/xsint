import argparse
import asyncio
import getpass
import importlib
import os
import shutil
import subprocess
import sys
from urllib.parse import urlparse

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

    if service == "gitfive":
        candidates.append([
            sys.executable, "-c",
            "from gitfive.lib.cli import parse_args; parse_args()", "login",
        ])
    else:
        candidates.append([sys.executable, "-m", service, "login"])

    local_bin = os.path.join(os.path.dirname(sys.executable), service)
    candidates.append([local_bin, "login"])

    which_path = shutil.which(service)
    if which_path:
        candidates.append([which_path, "login"])

    candidates.append([os.path.expanduser(f"~/.local/pipx/venvs/{service}/bin/{service}"), "login"])

    attempted = False
    for cmd in candidates:
        exe = cmd[0]
        if os.path.sep in exe and not (os.path.isfile(exe) and os.access(exe, os.X_OK)):
            continue
        try:
            attempted = True
            if subprocess.run(cmd).returncode == 0:
                return True, True
            return False, True
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
_RESET = "\033[0m"


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


HELP_TEXT = """\
xsint ( https://github.com/memorypudding/xsint )
Usage: xsint [Options] {target}

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

MISC:
  -h, --help: Print this help summary
"""


class _XsintParser(argparse.ArgumentParser):
    def format_help(self):
        return HELP_TEXT

    def format_usage(self):
        return "Usage: xsint [Options] {target}\n"


def main():
    parser = _XsintParser(prog="xsint", add_help=True)
    parser.add_argument("target", nargs="?")
    parser.add_argument("-m", "--modules", nargs="?", const="all", metavar="TYPE")
    parser.add_argument("--auth", nargs="*", metavar="ARGS")
    parser.add_argument("--proxy", metavar="URL")

    if len(sys.argv) == 1:
        print(HELP_TEXT, end="")
        return

    args = parser.parse_args()

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
        animate = sys.stdout.isatty()
        # name -> {status: "running"|"done", count: int, status_str: str}
        modules_state = {}
        spinner_stop = asyncio.Event()
        last_lines = [0]  # mutable so closures can update

        def _render():
            """Redraw the dashboard. TTY-only — non-TTY uses one-shot prints."""
            DOT_FRAMES = [".  ", ".. ", "...", " ..", "  .", "   "]
            frame = _render.frame = (getattr(_render, "frame", -1) + 1) % len(DOT_FRAMES)
            dots = DOT_FRAMES[frame]

            # Build lines in the order modules first appeared.
            lines = []
            for name, info in modules_state.items():
                if info["status"] == "running":
                    lines.append(f"[*] {name}: {dots}")
                else:
                    n = info["count"]
                    lines.append(f"[+] {name}: {n} result{'s' if n != 1 else ''}")

            buf = []
            if last_lines[0]:
                buf.append(f"\033[{last_lines[0]}A")
            for line in lines:
                buf.append("\r\033[2K" + line + "\n")
            sys.stdout.write("".join(buf))
            sys.stdout.flush()
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
                    sys.stdout.write(f"[*] {name}: ...\n")
                    sys.stdout.flush()
            elif kind == "module_done":
                ran_any = True
                count = int(event.get("count", 0) or 0)
                modules_state[name] = {"status": "done", "count": count}
                if animate:
                    _render()
                else:
                    suffix = "s" if count != 1 else ""
                    sys.stdout.write(f"[+] {name}: {count} result{suffix}\n")
                    sys.stdout.flush()

        async def _animator():
            while not spinner_stop.is_set():
                if any(info["status"] == "running" for info in modules_state.values()):
                    _render()
                try:
                    await asyncio.wait_for(spinner_stop.wait(), timeout=0.18)
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
            print(f"[!] {report['error'].splitlines()[0]}")
            return

        if not ran_any:
            print("[!] no eligible modules — run --auth to enable more, or check `xsint -m`")
            return

        if not (report.get("results") or []):
            print("[!] no intel found")
        else:
            print()
            print_results(report)
    finally:
        await engine.close()


if __name__ == "__main__":
    main()
