# Using xsint

So you've got `xsint` installed and you're wondering what to do with it. Good. Let's get into it.

## The Tao of xsint

Here's the entire pitch:

> You hand it one piece of public information about a person — an
> email, a username, a phone number, a street address — and it asks
> a bunch of websites and services *"hey, do you know about this?"*
> at the same time. Then it prints what came back.

That's it. That's the whole tool. The "magic" is just that doing this manually across 80 sources would take you all afternoon, and `xsint` does it in about ten seconds.

The thing it gives you back is called a **dossier** — a one-page summary of who, where, and what's been leaked. You can also ask for the raw stuff if you'd rather see it source-by-source, or get JSON if you're piping into something else.

## Your first scan

Run this:

```bash
xsint someone@example.com
```

Replace `someone@example.com` with whatever email you actually want to look at. (Run it on yourself first! That's a great way to see what `xsint` does without putting it on someone else.)

You'll see something like this scroll by:

```text
[*] email_enum: ...
[+] ghunt_lookup: 11 results
[-] gitfive_module: no results
[+] haxalot_module: 35 results
[+] nineghz: 7 results
```

Each line is one module — one of the sources `xsint` consults — reporting in. The little symbol at the start tells you what's going on:

| Symbol | Color  | What it means                       |
| :----: | ------ | ----------------------------------- |
| `[*]`  | yellow | Still working, hold on              |
| `[+]`  | green  | Done; found at least one thing      |
| `[-]`  | red    | Done; came up empty                 |

(If you don't see colors, your terminal probably isn't a TTY — running through a pipe, redirected to a file, that kind of thing. The symbols are still there, just not pretty.)

After everything finishes, you get the **dossier**.

## What does the dossier look like?

Glad you asked!

```text
  IDENTITY REPORT
  someone@example.com
  ──────────────────────────────────────────────────────────────────────
  type      email
  scanned   2026-05-06 15:39
  scope     4 sources · 10 breaches · 5 passwords · 2 hashes


  IDENTITY
  ────────
  name            Jane Doe                                       Google
                  Jane                                     Mathway, ATT
  github          12345678                                      GitFive

  ALIASES  ·  3
  ─────────────
                  janedoe2013                                     Canva
                  Jane_doe                                     Duolingo

  REGISTERED ACCOUNTS  ·  11
  ──────────────────────────
  Adobe · Amazon · Duolingo · Espn · GitHub · Office365 · Spotify · ...

  BREACH HISTORY  ·  10
  ─────────────────────
                  2023-08-01  Duolingo Scrape Database             9Ghz
                  2020-01-13  Mathway                     Haxalot, 9Ghz
                  ...

  CREDENTIALS LEAKED
  ──────────────────
  passwords (5)   somepassword                                  Mathway
                  hunter2                                         Canva
                  ...

  hashes (2)      $2a$10$3btf1EEjvH9...                           Canva
```

Each section answers a different question:

- **IDENTITY** — who is this? Names from authoritative sources (Google, GitHub) come first; names from breaches show up if multiple breaches agree on them.
- **ALIASES** — what handles do they use? Usernames, nicks, gamertags.
- **REGISTERED ACCOUNTS** — what services have they signed up for?
- **CONTACT** — phone numbers, IPs, alternate emails, mobile carriers.
- **LOCATIONS** — addresses and locations from breach records.
- **BREACH HISTORY** — every breach they've shown up in, dated where possible.
- **CREDENTIALS LEAKED** — passwords and password hashes, deduped, with the breach they came from.
- **ACTIVITY** — registration dates, account-status events, Google Maps stats.
- **LINKS** — URLs to profile pages.

The grey text on the right of each row is the **source** — which breach or service that piece of data came from. So when you see `Jane Doe ... Mathway, ATT`, that's saying: the Mathway breach AND the AT&T breach both have a record listing "Jane Doe" against this email.

That's the default view. It's called `--pretty`, even though you don't have to type that.

## "What if I want it different?"

There are four output formats. Just one is on by default; the rest you opt into with a flag.

### `--pretty` — the dossier (default)

You just saw it. Don't need to do anything. But you can still type `--pretty` if you want to be explicit, or to override an environment that defaulted you somewhere else.

### `--raw` — source-by-source dump

This is the un-synthesized view. Every module's output, grouped by module, exactly as the module wrote it down. Useful when you want to see what a specific source said, without my summary layer in the way.

```bash
xsint --raw someone@example.com
```

### `--json` — for piping

```bash
xsint --json someone@example.com > scan.json
```

Or, if you have `jq`:

```bash
xsint --json someone@example.com | jq '.results[] | select(.source=="9Ghz")'
```

Stdout becomes a JSON object. The progress dashboard goes to stderr, so your redirected stdout stays clean. Shape:

```json
{
  "target": "someone@example.com",
  "type": "email",
  "scanned_at": 1778103784,
  "findings": 28,
  "results": [
    { "label": "...", "value": "...", "source": "...", "group": "..." }
  ],
  "themes": { },
  "error": null
}
```

### `--html <PATH>` — for sharing

```bash
xsint --html report.html someone@example.com
```

Writes a self-contained HTML file (single page, embedded CSS, dark-mode aware) you can open in any browser. Same dossier sections, just rendered with chips for breaches, clickable links, and a colored highlight on leaked passwords.

(`--html` *requires* a path argument. If you typed `xsint --html target` we'd assume you wanted the HTML written to a file called `target` and there's no target left for the scan, which is silly. So we make you spell it out.)

## What kind of target?

`xsint` figures out what you've handed it most of the time. An `@` sign means email. Digits with a `+` means phone. Four numbers separated by dots means IP. And so on.

When the guess might be wrong — or when the value is genuinely ambiguous — you can force it with a prefix:

```bash
xsint email:someone@example.com
xsint user:johndoe
xsint phone:+14155551234
xsint ip:8.8.8.8
xsint "addr:1600 Pennsylvania Ave NW, Washington, DC"
xsint hash:5f4dcc3b5aa765d61d8327deb882cf99
xsint "name:Jane Doe"
xsint id:1234567890
xsint ssn:123-45-6789
xsint passport:AB1234567
```

(Yes, you really can search for a literal hash. `xsint` will check it against breach databases. Useful when someone hands you a leaked password hash and you want to know if it's been seen before.)

If your target has spaces in it, wrap the whole thing in quotes — that's just a shell thing, not an `xsint` thing.

## "Nothing happened. What gives?"

A few possibilities:

**Every module ran but came up empty.** You'll see:

```text
[!] no intel found
```

That genuinely is what it sounds like. The target either doesn't exist on any of these services, or what's there is private enough that none of the public APIs will tell us about it. Try a different angle (do you have their phone? An old username?).

**Nothing was eligible to run.** Like:

```text
[!] no eligible modules — run --auth to enable more, or check `xsint -m`
```

This means every module that *could* handle your target type is locked behind a credential you haven't set up yet. Run `xsint --auth` to see what's missing, or `xsint -m <type>` to see what would handle this kind of target. Setting up credentials is a one-time thing — see [auth.md](auth.md).

**Something errored.** Each module is on its own clock — if one crashes, the others keep going. The crash shows up as an `[!]` line in the dashboard or as an `Error` finding in the report. (Almost always a network glitch. Run it again.)

## The module list

You can ask `xsint` to show its toolbox:

```bash
xsint -m
```

This prints a table of every module — name, where it comes from (`custom` means I wrote it; `external` means it wraps a third-party tool), whether it's `active` or `locked`, and which input types it handles.

If you want to know what would actually run on, say, a phone number:

```bash
xsint -m phone
```

That filters to just the phone-handling modules.

## "Can I make it slow down?"

Each module has a 25-second budget by default. If a module is taking too long (slow proxy, flaky network), it gets cut off and reported as a `Timeout`. Bump the budget if you need to:

```bash
XSINT_MODULE_TIMEOUT=60 xsint someone@example.com
```

(That's 60 seconds.)

## All the flags, for reference

```text
xsint 0.1.4.a ( https://github.com/h1lw/xsint )
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

OUTPUT FORMAT (mutually exclusive; default --pretty):
  --pretty      : Synthesized identity dossier (default)
  --raw         : Plain text dump grouped by source
  --json        : Full report as JSON (pipe to a file or another tool)
  --html <PATH> : Self-contained HTML report written to PATH

MISC:
  -V, --version: Print xsint version and exit
      --no-version-check: Skip the GitHub update check for this run
  -h, --help: Print this help summary
```

That's the whole CLI. Once you've used it a few times you'll have most of it memorized.

## Where to go from here

- Need a richer scan? Some modules need credentials — see [auth.md](auth.md).
- Curious which modules do what? See [modules.md](modules.md).
- Want everything to go through a proxy? See [proxy.md](proxy.md).
- Want to write your own module? See [development.md](development.md).
