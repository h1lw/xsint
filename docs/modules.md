# Modules

A module is one source — one website, API, or third-party tool — that `xsint` queries on your behalf. When you run a scan, every module that can handle your target type runs concurrently. The dossier you see at the end is everyone's findings stitched together.

This page is the rundown of who's in the toolbox.

## Run-time view

Before you read further: `xsint -m` will print this same list at runtime, with the *live* `active` / `locked` status for each module on *your* setup. If you want to know what'll actually run, that command is the source of truth. The table below is for orientation.

```bash
xsint -m            # everything
xsint -m email      # just the modules that handle emails
xsint -m phone      # just phones
```

## The list

| Name             | Source   | Handles                                                    | Returns                                                      | Setup                |
| ---------------- | -------- | ---------------------------------------------------------- | ------------------------------------------------------------ | -------------------- |
| `email_enum`     | custom   | email                                                      | account hits across 67 services in 18 categories             | none                 |
| `phone_enum`     | custom   | phone                                                      | account hits on Amazon, Snapchat                             | none                 |
| `phone_basic`    | custom   | phone                                                      | country, carrier, line type, timezone, normalized formats    | none                 |
| `instagram`      | custom   | username                                                   | recovery hints (masked email/phone) from IG's recovery flow  | none                 |
| `ip_basic`       | external | ip                                                         | IPv4/IPv6 detection, public/private classification           | none                 |
| `osm`            | external | address                                                    | geocoded address + coordinates via OpenStreetMap             | none                 |
| `nineghz`        | external | email, phone, username, ip, hash, name, id, ssn, passport  | breach hits                                                  | none (key optional)  |
| `hibp`           | external | email, username, phone, hash                               | breach names + dates                                         | API key              |
| `intelx`         | external | email, username, phone                                     | leaks, pastes, documents                                     | API key              |
| `haxalot_module` | external | email, username, phone, ip                                 | breaches, leaked passwords/hashes, scattered PII             | Telegram setup       |
| `ghunt_lookup`   | external | email, phone, gaia_id                                      | Google profile (Gaia ID, photo, Maps activity)               | Google login         |
| `gitfive_module` | external | email, username                                            | GitHub profile, occasionally a private email                 | GitHub login         |

## What "source" means

- **custom** — I wrote it. Lives inside `xsint/modules/`. If you want to read or modify a module, the custom ones are the easy targets.
- **external** — wraps somebody else's tool. Either an API client (`hibp`, `intelx`, `nineghz`) or a wrapper around a tool that has its own login (`ghunt`, `gitfive`).

Both kinds work the same from the user's perspective — they just take the target and return findings. The distinction only matters when you're debugging or installing.

## What "Setup" means

This is the column that tells you whether you can use the module right away or whether you have to do a one-time configuration step:

- **none** — works immediately after install. Just run a scan.
- **API key** — sign up somewhere, paste the key with `xsint --auth <module> <key>`.
- **login** — interactive browser-based login the first time (Google or GitHub).
- **Telegram setup** — you log into Telegram once with your phone + OTP.
- **(optional)** — module works without setup but does *more* with it.

The full how-to for each one is in [auth.md](auth.md).

## Active vs. locked

When you run `xsint -m`, every module shows up as either `active` (will run) or `locked` (will be skipped).

A module is **locked** when one of these is true:

1. **It needs a credential you haven't set up.** (Most common case.)
2. **Its underlying tool isn't installed.** Mainly `ghunt` and `gitfive` — if those binaries aren't on your system, the modules that wrap them are dead. The installer normally sets them up; if something went wrong there, see [auth.md](auth.md) for the manual install commands.
3. **Its `is_ready()` self-check returned false.** Each module gets to decide for itself whether it's runnable. For example, `haxalot_module` checks whether the Telegram session file exists.

Locked modules are silently skipped during scans — they don't crash anything, they just don't contribute findings.

## "Why so many breach modules?"

Reasonable question. We've got `hibp`, `intelx`, `nineghz`, `haxalot` — all looking up breaches. Why not just one?

Because each one has different data.

- HaveIBeenPwned has the cleanest, best-curated set, but only the metadata (which breach, when).
- IntelligenceX has individual leaked records (paste content, document fragments).
- 9Ghz has a wider corpus but less curation.
- Haxalot has the deepest corpus, including very recent and very obscure dumps, plus actual leaked passwords and hashes that the others won't surface.

In practice, when you scan an email, each module hits a different overlap of breaches. The dossier merges across all four — when two of them confirm the same breach, you'll see both names attributed in the report (`Mathway [Haxalot, 9Ghz]`).

## "Why is haxalot so much more powerful?"

Because it's a Telegram bot, not a public API. Public APIs (HIBP, IntelX, etc.) are bound by what their operators are willing to legally publish. The bot is gray-market — it has more data because it's allowed to have more data, where "allowed" is doing a lot of work.

Use it with that context in mind. It's tremendously useful for OSINT, but the data has been redistributed in ways that not all of it strictly should have been. Don't be a jerk with what comes out.

## Reading the module table

The columns:

- **Name** — what to use in `--auth` and what shows up in the dashboard.
- **Source** — `custom` or `external` as discussed.
- **Handles** — the input types this module can answer questions about. If your target is an email and a module's `handles` doesn't include `email`, that module won't run for this scan.
- **Returns** — the rough categories of data you might see in the dossier when this module runs.
- **Setup** — what you have to do once to enable it.

Here's the CLI version of the same info:

```bash
xsint -m
```

Outputs a colorized table — green for `active`, red for `locked` — with the same columns plus the resolved status. Use this rather than the table on this page when you're debugging "why didn't X run?".
