# Going through a proxy

Maybe you don't want every breach-search service to see your home IP. Maybe you're testing through Burp Suite. Maybe you're routing through Tor for anonymity, or through a corporate gateway because you're on a work laptop. Whatever the reason, `xsint` has a single flag for it.

## The basic move

```bash
xsint --proxy socks5://127.0.0.1:9050 someone@example.com
```

That's it. Every module's HTTP traffic will go through that proxy for this run. SOCKS5 example above (Tor's default port), but HTTP and SOCKS4 work too:

```bash
xsint --proxy http://127.0.0.1:8080 someone@example.com   # Burp / mitmproxy / corporate proxy
xsint --proxy socks5://127.0.0.1:9050 someone@example.com # Tor
xsint --proxy socks4://1.2.3.4:1080  someone@example.com  # uncommon but supported
```

`xsint` validates the URL and tries to actually open a TCP connection to it before starting the scan. If your proxy isn't running, you find out *immediately* — it bails with a clear error rather than silently going direct. (That's an important property for the privacy use cases. If you asked for Tor and Tor's down, you want to know before traffic leaks out the front door.)

## Make it permanent

Don't want to type the flag every time? Set an environment variable:

```bash
export XSINT_PROXY=socks5://127.0.0.1:9050
```

Stick that line in `~/.zshrc` or `~/.bashrc` (or wherever your shell reads its startup config) and every new terminal session has the proxy set. If you ever want to override for one run, the `--proxy` flag wins:

```bash
xsint --proxy http://127.0.0.1:8080 someone@example.com   # uses Burp for this run
xsint someone@example.com                                  # back to env var
```

## Resolution order

For the curious. When `xsint` builds its HTTP session, it checks (in order):

1. The `--proxy` flag if you used one
2. `XSINT_PROXY` environment variable
3. The `proxy` field in `./config.json`
4. Direct connection (no proxy)

First one that's set wins. The others get ignored.

## A weird thing about TLS

Burp, mitmproxy, ZAP — interception proxies — work by impersonating the destination server's TLS certificate. They sign their fake cert with their own self-signed CA, which your browser is supposed to trust. Python's TLS library doesn't trust that CA out of the box, so normally every module would fail with a certificate error.

To save you from manually configuring a CA bundle, `xsint` automatically disables TLS verification when `--proxy` (or `XSINT_PROXY`) is set. Modules send unverified HTTPS through the proxy.

This is the right default for the use case — if you've got Burp running locally to inspect your own traffic, you don't want every module to fail because of cert verification — but it does mean: **don't point `--proxy` at an endpoint you don't trust.** A malicious proxy could read everything you're sending.

(In practice you're probably either using your own local proxy or a Tor entry node. Both are fine.)

## "But I want to verify certs"

If you really want strict verification, configure your proxy's CA bundle in your Python environment (`SSL_CERT_FILE`, `requests` CA bundle, etc.) and `xsint` will use it. Not exactly a one-liner, but possible.

## Does every module honor the proxy?

Almost. The catch:

- **Custom modules** (the ones inside `xsint/modules/` that I wrote) all use the shared HTTP session, which gets the proxy applied automatically. ✓
- **API-wrapping external modules** (`hibp`, `intelx`, `nineghz`) also use the shared session. ✓
- **`ghunt` and `gitfive`** are different. They're third-party tools with their own HTTP clients that we just call into. `xsint` injects the standard `HTTP_PROXY` / `HTTPS_PROXY` / `ALL_PROXY` environment variables before invoking them, so well-behaved tools pick the proxy up automatically. Both ghunt and gitfive currently respect those env vars, but if you find traffic missing from your interceptor, that's the place to look.

## Tor specifically

```bash
xsint --proxy socks5://127.0.0.1:9050 someone@example.com
```

Two things to expect:

1. **It's slow.** Tor adds 1-3 seconds of latency per request and many of these modules fan out to dozens of HTTP requests. Plan on 30-60 seconds for a full scan over Tor versus 5-15 seconds direct.

2. **Some services rate-limit Tor exits aggressively.** Spotify, Amazon, a few others may either CAPTCHA you or just return 429 for everything. Those'll show up in the dossier as "rate limited" findings rather than registered/not-registered. That's normal for Tor — try a different exit (restart Tor) if you're getting hammered.

## Common problems

**"proxy unreachable"** — `xsint` couldn't open a TCP connection to the proxy address you gave. Most likely the proxy isn't running, the port is wrong, or a firewall's in the way.

**"TLS / certificate error"** despite using `--proxy` — that means a module bypassed the auto-verify-disable. Open an issue with the module name and the URL it was hitting.

**Scan worked direct, fails with proxy** — usually a sign the proxy is forwarding to the wrong place. Check Burp's logs / Tor's logs.

**ghunt or gitfive traffic isn't in my proxy log** — see the section above. They use env vars; double-check those are set in the same shell where you ran `xsint`.

## Sanity check

A quick way to verify your proxy is actually being used:

```bash
xsint --proxy http://127.0.0.1:8080 ip:1.2.3.4
```

Watch your Burp / mitmproxy / Tor log. You should see `xsint`'s requests show up there.
