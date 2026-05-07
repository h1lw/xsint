# Connecting accounts

Most of `xsint` works out of the box — `email_enum`, `phone_basic`, `phone_enum`, `nineghz`, `ip_basic`, `osm`, and `instagram` need no setup. The richer modules need credentials, which you only have to set once.

## Quick check: what's connected?

```bash
xsint --auth
```

Prints a table of every gated module, whether it's set up, and what to run if it isn't.

## At a glance

| Module          | Service             | How to enable                              |
| --------------- | ------------------- | ------------------------------------------ |
| `hibp`          | HaveIBeenPwned      | `xsint --auth hibp YOUR_KEY`               |
| `intelx`        | IntelligenceX       | `xsint --auth intelx YOUR_KEY`             |
| `9ghz`          | 9Ghz (optional)     | `xsint --auth 9ghz YOUR_KEY` *(works without one)* |
| `ghunt_lookup`  | Google              | `xsint --auth ghunt`                       |
| `gitfive_module` | GitHub             | `xsint --auth gitfive`                     |
| `haxalot_module` | Telegram bot       | `xsint --auth haxalot`                     |

All gated modules are **off by default** — they show up as `locked` in `xsint -m` and are skipped during scans until you've enabled them.

## API keys

For HaveIBeenPwned, IntelligenceX, and 9Ghz, sign up at the service, grab your key, and:

```bash
xsint --auth hibp YOUR_HIBP_KEY
xsint --auth intelx YOUR_INTELX_KEY
xsint --auth 9ghz YOUR_9GHZ_KEY
```

Keys go into `./config.json` in the directory where you run the command. Plain JSON — edit it by hand if you ever need to.

### Overriding without editing the file

Set the matching environment variable; it wins over `config.json`:

```bash
export XSINT_HIBP_API_KEY=abcd1234
export XSINT_INTELX_API_KEY=...
export XSINT_9GHZ_API_KEY=...
```

Order of resolution:

1. `XSINT_<SERVICE>_API_KEY` env var
2. `<service>_key` field in `config.json`
3. Otherwise treated as missing

### A note on 9Ghz

9Ghz works without a key — it just hits the public `/api/v1/query` endpoint. With a key it gets bumped to `/api/v1/query_detail` which returns richer breach metadata. You can leave it unset.

## Google login (`ghunt`)

```bash
xsint --auth ghunt
```

This shells out to ghunt's own login flow. It walks you through pasting in your Google session cookies (ghunt's docs explain how — you log into Google in a browser, then copy a few cookies). The session is stored in `~/.malfrats/ghunt/`.

`xsint` looks for ghunt in this order: a `ghunt` binary on your `PATH`, then a pipx venv, then the same Python interpreter `xsint` was installed with. If none of those work, install ghunt first (`pipx install ghunt` or `pip install --user ghunt`) and try again.

## GitHub login (`gitfive`)

```bash
xsint --auth gitfive
```

Same idea as ghunt — gitfive has its own login flow. You'll need a GitHub account and a personal access token (gitfive's docs explain). Session is stored in `~/.gitfive/`.

## Telegram setup (`haxalot`)

```bash
xsint --auth haxalot
```

This one is a Telegram bot, not an API. Setup walks you through:

1. Entering your phone number.
2. Entering the OTP that Telegram sends to your app.

Once it's authenticated, the session lives in `~/.config/xsint/haxalot_session.session`. The bot does the heavy lifting at lookup time — `xsint` just messages it and parses the reply.

If you ever want to start over: delete that session file and re-run `xsint --auth haxalot`.

## Where credentials live

| File                                              | Owned by         | What's in it                |
| ------------------------------------------------- | ---------------- | --------------------------- |
| `./config.json`                                   | `xsint`          | API keys (HIBP, IntelX, 9Ghz) |
| `~/.malfrats/ghunt/`                              | ghunt (upstream) | Google session cookies      |
| `~/.gitfive/`                                     | gitfive (upstream) | GitHub session             |
| `~/.config/xsint/haxalot_session.session`         | telethon          | Haxalot Telegram session    |

Nothing in there leaves your machine. `xsint` runs every check from your local connection (or your proxy — see [proxy.md](proxy.md)).
