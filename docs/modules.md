# Modules

Each module is one source — a website, an API, or a third-party tool — that `xsint` queries on your behalf. Run `xsint -m` to see this list at runtime with the live `active` / `locked` status of each.

## What's available

| Name             | Source   | Input types                                                | What it returns                                  | Setup                |
| ---------------- | -------- | ---------------------------------------------------------- | ------------------------------------------------ | -------------------- |
| `email_enum`     | custom   | email                                                      | registered accounts on 67 services across 18 categories | none           |
| `phone_enum`     | custom   | phone                                                      | registered accounts on Amazon, Snapchat          | none                 |
| `phone_basic`    | custom   | phone                                                      | formats, country, carrier, line type, timezone   | none                 |
| `instagram`      | custom   | username                                                   | account-recovery hints (masked email/phone)      | none                 |
| `ip_basic`       | external | ip                                                         | version, public/private classification           | none                 |
| `osm`            | external | address                                                    | geocoded address, coordinates, location type     | none                 |
| `nineghz`        | external | email, phone, username, ip, hash, name, id, ssn, passport  | breach hits                                      | none (key optional)  |
| `hibp`           | external | email, username, phone, hash                               | breach hits with names + dates                   | API key              |
| `intelx`         | external | email, username, phone                                     | leaks, pastes, documents                         | API key              |
| `haxalot_module` | external | email, username, phone, ip                                 | breaches, leaked passwords/hashes, scattered PII | Telegram setup       |
| `ghunt_lookup`   | external | email, phone, gaia_id                                      | Google profile (Gaia ID, photo, Maps activity)   | Google login         |
| `gitfive_module` | external | email, username                                            | GitHub profile, resolved private email           | GitHub login         |

## Source

- **custom** — implemented inside `xsint/modules/`. Easy to read, easy to fork.
- **external** — wraps a third-party tool or API.

## Setup

- **none** — runs as soon as `xsint` is installed.
- **API key** — set with `xsint --auth <service> <key>` or `XSINT_<SERVICE>_API_KEY` env var.
- **Telegram setup / Google login / GitHub login** — interactive flow you run once. See [auth.md](auth.md).

A module that needs setup but hasn't gotten it shows up as `locked` in `xsint -m`. Locked modules are skipped during scans — the scan still runs everything else.

## active vs locked

`active` means the module is ready to run for the given target type. `locked` means one of these is true:

- The target type only works with a paid key, and no key is configured.
- A required dependency isn't installed (`ghunt`, `gitfive`).
- The module's `is_ready()` self-check returned false (e.g. login session is missing or expired).

`xsint -m <type>` filters the table to just modules that handle a given input type — handy for finding what would run on, say, a phone number:

```bash
xsint -m phone
```
