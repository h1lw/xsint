# Connecting accounts

A confession up front: not every module in `xsint` works out of the box. Some need credentials. **But most don't.**

If you just installed `xsint` and ran it on yourself and got a real-looking report — congratulations, you're already getting a lot for free. The modules that work without any setup are:

- `email_enum` — checks if your email is registered on 67 different services
- `phone_enum` — same idea, for phone numbers
- `phone_basic` — geographic and carrier metadata for a phone number
- `instagram` — looks at Instagram's account-recovery flow for hints
- `nineghz` — breach lookups (works without a key, better with one)
- `ip_basic` — basic IP info
- `osm` — geocodes addresses

That's a lot! The rest of this page is about the *other* modules — the ones that need a one-time setup before they'll do anything.

## Quick check: what's connected?

```bash
xsint --auth
```

This prints a table showing every credential-gated module, whether it's set up, and what to type if it isn't. No surprises. Good place to start.

## At a glance

| Module           | What it talks to     | How to enable                                       |
| ---------------- | -------------------- | --------------------------------------------------- |
| `hibp`           | HaveIBeenPwned       | `xsint --auth hibp YOUR_KEY`                        |
| `intelx`         | IntelligenceX        | `xsint --auth intelx YOUR_KEY`                      |
| `9ghz`           | 9Ghz (optional!)     | `xsint --auth 9ghz YOUR_KEY` *(works keyless too)*  |
| `ghunt_lookup`   | Google               | `xsint --auth ghunt`                                |
| `gitfive_module` | GitHub               | `xsint --auth gitfive`                              |
| `haxalot_module` | A Telegram bot       | `xsint --auth haxalot`                              |

Until you've set them up, these modules show as `locked` in `xsint -m`, and `xsint` skips them during scans.

## API keys (the easy ones)

Three modules — `hibp`, `intelx`, `9ghz` — are HTTP APIs that you authenticate with a string of letters and numbers. You sign up at the service's website, copy your key, paste it into one command.

```bash
xsint --auth hibp YOUR_HIBP_KEY
xsint --auth intelx YOUR_INTELX_KEY
xsint --auth 9ghz YOUR_9GHZ_KEY
```

The keys go into a file called `config.json` in whatever directory you ran the command from. It's just JSON. You can edit it by hand if you ever need to.

> **Heads up:** `config.json` lives in the *current working directory*, not in your home folder. If you set a key from `~/projects/foo/` and then run `xsint` from `~/`, the key won't follow you. The fix is to either always run from the same place, or use the env-var approach below — that one *does* follow you.

### Env vars, for when you want it to follow you everywhere

Every API key has a matching environment variable that overrides `config.json`:

```bash
export XSINT_HIBP_API_KEY=abcd1234
export XSINT_INTELX_API_KEY=...
export XSINT_9GHZ_API_KEY=...
```

Stick those in your `.zshrc` or `.bashrc` and you're done forever.

The resolution order:

1. Env var `XSINT_<SERVICE>_API_KEY`
2. `<service>_key` field in `config.json`
3. Otherwise, treated as missing — module locks itself

### About 9Ghz

Plot twist: 9Ghz works without a key. The keyless endpoint (`/api/v1/query`) returns basic breach hits. With a key, you get bumped up to `/api/v1/query_detail`, which returns *more* data per breach (timestamps, source URLs, that kind of thing). So a key is nice but you can absolutely leave it unset.

That's why the table above says "(optional!)".

## Google login (`ghunt`)

`ghunt` is its own tool, written by mxrch. `xsint` wraps it. To use it you need to be logged into Google through `ghunt`'s own login flow.

```bash
xsint --auth ghunt
```

What this actually does: it shells out to ghunt's own login command. Ghunt walks you through pasting in your Google session cookies. (You log into Google in a browser, open dev tools, copy a few cookies, paste them. Ghunt's own docs explain it better than I will.)

The session ends up in `~/.malfrats/ghunt/`. After that one-time setup, `xsint --auth ghunt` would just say "already logged in" and you can move on.

### "It said it can't find ghunt"

The installer should have set this up, but if you're seeing "ghunt not found", you're missing the binary. Install it:

```bash
pipx install ghunt
# or
pip install --user ghunt
```

`xsint` looks for `ghunt` in this order:

1. Whatever `ghunt` resolves to on `PATH`
2. A `ghunt` in `~/.local/pipx/venvs/ghunt/bin/`
3. A `ghunt` next to the same Python interpreter `xsint` was installed with

If none of those work, you'll get a friendly error.

## GitHub login (`gitfive`)

Same author, same idea, different service.

```bash
xsint --auth gitfive
```

Walks you through gitfive's login flow. You'll need a GitHub account and a Personal Access Token (a long string of letters from GitHub Settings → Developer Settings → Tokens). Gitfive's docs spell out which token scopes it wants.

Session lands in `~/.gitfive/`.

## Telegram bot (`haxalot`)

This one's a bit different. There's a Telegram bot called haxalot that does breach searches. `xsint` talks to it via the Telegram API as a regular user.

```bash
xsint --auth haxalot
```

The setup walks you through:

1. Type your phone number (the one you use for Telegram)
2. Type the OTP that Telegram sends you in-app

Telegram sends back a session token that gets saved to `~/.config/xsint/haxalot_session.session`. After that, `xsint` re-uses the session for every scan — no more OTPs.

Once it's set up, this is the most powerful module by far. Haxalot has a *huge* breach corpus. Expect 100+ findings on common emails.

> **What this does and doesn't do:**
> - It logs you into Telegram so `xsint` can DM the haxalot bot from your account.
> - It does *not* read your messages, contacts, anything else. Look at the source — it just sends a query and parses the reply.
> - The session is stored on your machine. Don't share it.

If you ever want to start over (lost session, switched phones, whatever), delete `~/.config/xsint/haxalot_session.session` and re-run `xsint --auth haxalot`.

## Where credentials live

So you know what's where:

| File                                              | Owned by         | What's in it                |
| ------------------------------------------------- | ---------------- | --------------------------- |
| `./config.json`                                   | `xsint`          | API keys                    |
| `~/.malfrats/ghunt/`                              | ghunt            | Google session cookies      |
| `~/.gitfive/`                                     | gitfive          | GitHub session              |
| `~/.config/xsint/haxalot_session.session`         | telethon         | Telegram session for haxalot |

None of this leaves your machine. `xsint` runs every module from your local Python — there's no `xsint.com` API in between.

## "I changed my password / GitHub is mad / something stopped working"

If a session expires (Google logged you out, etc.), the affected module will start showing up as `locked` again. Re-run `xsint --auth <module>` and it'll re-do the login flow.

Nothing in `xsint` will silently use stale credentials.
