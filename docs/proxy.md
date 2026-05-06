# Proxy

`xsint` routes all module HTTP traffic through a single proxy when configured. HTTP, SOCKS4, and SOCKS5 are supported (via `aiohttp-socks`).

## Per-run

```bash
xsint --proxy socks5://127.0.0.1:9050 user@example.com
xsint --proxy http://127.0.0.1:8080 user@example.com
```

The URL is validated before the scan starts; bad URLs exit non-zero with an error.

## Persistent

Set the environment variable in your shell profile:

```bash
export XSINT_PROXY=socks5://127.0.0.1:9050
```

The env var takes effect for every `xsint` invocation. `--proxy <URL>` on the command line overrides it for that run.

## Resolution order

When the engine builds its HTTP session, it picks the proxy from:

1. `--proxy` CLI argument
2. `XSINT_PROXY` environment variable
3. `proxy` field in `config.json`
4. Direct connection (no proxy)

## Troubleshooting

If proxy setup fails (unreachable host, malformed URL slipping past validation, missing `aiohttp-socks` extras), `xsint` falls back to a direct connection and prints a warning. Modules that bypass the shared session — for example, third-party tools like `ghunt` that manage their own HTTP client — may not honour the proxy. Configure those tools' own proxy settings separately if needed.
