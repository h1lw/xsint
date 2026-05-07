# Usage

The short version: hand `xsint` whatever you have and let it figure out the rest.

```bash
xsint someone@example.com
xsint +14155551234
xsint johndoe
xsint 8.8.8.8
```

A clean dossier prints to your terminal a few seconds later. If you want a different shape — JSON for piping, HTML for sharing — there's a flag for that.

## All the flags

```text
xsint 0.1.3 ( https://github.com/h1lw/xsint )
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

## Forcing a target type

`xsint` auto-detects the kind of thing you've given it. If the guess is wrong, prefix the target:

```bash
xsint email:someone@example.com
xsint user:johndoe
xsint phone:+14155551234
xsint ip:8.8.8.8
xsint "addr:1600 Pennsylvania Ave NW, Washington, DC"
xsint hash:5f4dcc3b5aa765d61d8327deb882cf99
xsint "name:John Doe"
xsint id:1234567890
xsint ssn:123-45-6789
xsint passport:AB1234567
```

## Output formats

By default `xsint` prints a synthesized **identity report** — names, accounts, breach exposure, leaked credentials, all deduped across sources. That's `--pretty`. The other three formats trade that report off for something more machine-friendly.

### `--pretty` (default)

```text
  IDENTITY REPORT
  someone@example.com
  ──────────────────────────────────────────────────────────────────────────
  type      email
  scanned   2026-05-06 15:39
  scope     4 sources · 10 breaches · 5 passwords · 2 hashes


  IDENTITY
  ────────
  name            John Doe                                              Google
                  John                                            Mathway, ATT
  github          12345678                                             GitFive

  ALIASES  ·  3
  ─────────────
                  johndoe2013                                            Canva
                  John_doe                                            Duolingo

  REGISTERED ACCOUNTS  ·  11
  ──────────────────────────
  Adobe · Amazon · Duolingo · Espn · GitHub · Office365 · Pinterest · Spotify

  BREACH HISTORY  ·  10
  ─────────────────────
                  2023-08-01  Duolingo Scrape Database                    9Ghz
                  2020-01-13  Mathway                            Haxalot, 9Ghz
                  2019-05-24  Canva                              Haxalot, 9Ghz
                  ...

  CREDENTIALS LEAKED
  ──────────────────
  passwords (5)   somepassword                                         Mathway
                  hunter2                                                Canva
                  ...

  hashes (2)      $2a$10$3btf1EEjvH9...                                  Canva
```

Section headers are bold and source attributions are dimmed grey when stdout is a terminal. Pipe it (`xsint ... | less`) and you get plain text instead.

### `--raw`

The legacy source-by-source dump. Useful when you want to see exactly what each module returned without the synthesis layer:

```bash
xsint --raw user@example.com
```

```text
type     : EMAIL
findings : 28
sources  : 4

9Ghz (2)
  Breaches : 1
  Breach   : Adobe (2013-10-04)

EmailEnum (11)
  Creator / Adobe       : registered (https://adobe.com)
  Dev / Github          : registered (https://github.com)
  ...

GHunt (11)
  👤 Account / Gaia ID  : 113877113026769046726
  👤 Account / Name     : Some Person
  ...
```

### `--json`

Stdout becomes a JSON object — convenient for piping into `jq`, saving for later, or feeding another tool:

```bash
xsint --json user@example.com > scan.json
xsint --json user@example.com | jq '.results[] | select(.source=="9Ghz")'
```

The JSON shape:

```json
{
  "target": "user@example.com",
  "type": "email",
  "scanned_at": 1778103784,
  "findings": 28,
  "results": [
    { "label": "...", "value": "...", "source": "...", "group": "...", "risk": "..." },
    ...
  ],
  "themes": { ... },
  "error": null
}
```

The progress dashboard goes to **stderr** under `--json`, so the redirected stdout stays clean.

### `--html <PATH>`

Writes a self-contained HTML page (embedded CSS, dark-mode aware) to the path you give it:

```bash
xsint --html report.html user@example.com
```

The same identity-dossier layout as `--pretty`, but rendered as a webpage with chip tags for breaches, clickable links, monospaced hashes, and a colored highlight on leaked passwords. Open it in any browser. Good for sharing or archiving.

## What runs while it's running

```text
[*] email_enum: ...
[+] ghunt_lookup: 11 results
[-] gitfive_module: no results
[+] haxalot_module: 35 results
[+] nineghz: 7 results
```

The prefixes are color-coded on a TTY:

| Prefix | Color | Meaning                                  |
| ------ | ----- | ---------------------------------------- |
| `[*]`  | yellow | Module is still running.                |
| `[+]`  | green  | Done — found at least one result.       |
| `[-]`  | red    | Done — found nothing.                   |

The dots after `[*]` are an animated spinner, each module pacing independently.

## When nothing comes back

If every available module ran but returned nothing:

```text
[!] no intel found
```

If everything was locked (no auth configured for the target type):

```text
[!] no eligible modules — run --auth to enable more, or check `xsint -m`
```

Run `xsint -m` to see which modules are active and which are locked.

## Listing modules

```bash
# Everything
xsint -m

# Just the modules that handle a specific target type
xsint -m email
xsint -m phone
xsint -m username
```

The output table shows `name`, `source` (custom vs external dependency), `status` (active in green, locked in red), and the input types each module supports. A locked module either needs credentials (see [auth.md](auth.md)) or its underlying tool isn't installed.

## Tweaking timeouts

Each module is wrapped in a 25-second timeout by default. Override with:

```bash
XSINT_MODULE_TIMEOUT=60 xsint user@example.com
```

A module that exceeds its budget shows up as a `Timeout` finding rather than crashing the whole scan.
