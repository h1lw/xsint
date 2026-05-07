# Proxy

Want every request to go through Tor, Burp, or any other proxy? One flag.

```bash
xsint --proxy socks5://127.0.0.1:9050 user@example.com
xsint --proxy http://127.0.0.1:8080 user@example.com
```

`xsint` validates the URL up-front and pings it before the scan starts. If the proxy is unreachable, the scan exits non-zero with an error rather than silently going direct.

## Make it stick

To proxy every run without typing the flag, set `XSINT_PROXY` in your shell profile:

```bash
export XSINT_PROXY=socks5://127.0.0.1:9050
```

Pick where to put that based on your shell — `~/.zshrc`, `~/.bashrc`, etc.

A `--proxy` flag on the command line wins over the environment variable, so you can override per-run when needed.

## How a proxy is chosen

When the engine sets up its HTTP session, it picks the first one of these that's set:

1. `--proxy` argument
2. `XSINT_PROXY` environment variable
3. `proxy` field in `./config.json`
4. Direct connection (no proxy)

## Supported schemes

- `http://` and `https://` — any HTTP proxy. Burp Suite, mitmproxy, corporate proxies.
- `socks4://` and `socks5://` — handled via `aiohttp-socks`. Tor uses SOCKS5 on `127.0.0.1:9050`.

## Self-signed CA (Burp, mitmproxy, ZAP)

Intercept proxies present a self-signed CA, which would normally trip TLS verification on every module. When `--proxy` is set, `xsint` automatically disables TLS verification for outbound requests so the proxy can do its work. This is the right default for the use case but it does mean: **don't use `--proxy` with an untrusted endpoint.**

## Modules that bypass the proxy

A handful of upstream tools (`ghunt`, `gitfive`) manage their own HTTP clients and don't always honor the shared session. `xsint` injects `HTTP_PROXY` / `HTTPS_PROXY` / `ALL_PROXY` into the environment so well-behaved tools pick it up — but if a module's traffic is missing from your interceptor, configure that module's proxy settings directly.

## Troubleshooting

- **"proxy unreachable"** — `xsint` couldn't even open a TCP connection. The proxy isn't running, or it's running on a different port, or a firewall is in the way.
- **TLS errors despite `--proxy`** — that means our verify-disable patch missed a code path. File an issue with the module name.
- **Scan is slow** — Tor is slow. SOCKS5 over Tor adds latency and many of the modules fan out to dozens of HTTP requests. Expect 30–60s for a full scan over Tor versus 5–15s direct.
