# Modules

`xsint -m` prints this list at runtime, with current `active` / `locked` status. `xsint -m <type>` filters to modules that handle a given input type.

| Name             | Source   | Input Types                                               | Returns                                            | Auth                |
| ---------------- | -------- | --------------------------------------------------------- | -------------------------------------------------- | ------------------- |
| `instagram`      | custom   | username                                                  | recovery methods                                   | none                |
| `phone_basic`    | custom   | phone                                                     | formats, country, carrier, line type, timezone    | none                |
| `email_enum`     | custom   | email                                                     | registered accounts (67 services across 18 categories)     | none      |
| `phone_enum`     | custom   | phone                                                     | registered accounts (Amazon, Instagram, Snapchat)         | none      |
| `ip_basic`       | external | ip                                                        | version, private/public                            | none                |
| `osm`            | external | address                                                   | address, coordinates, location type                | none                |
| `hibp`           | external | email, username, phone, hash                              | breaches, breach names, breach dates               | api key             |
| `intelx`         | external | email, username, phone                                    | breaches, leaks, pastes, documents                 | api key             |
| `nineghz`        | external | email, username, phone, ip, hash, name, id, ssn, passport | breaches                                           | api key             |
| `haxalot_module` | external | email, username, phone, ip                                | breaches, passwords, pii                           | setup               |
| `ghunt_lookup`   | external | email, phone, gaia_id                                     | gaia_id, profile, services, maps, calendar         | login               |
| `gitfive_module` | external | email, username                                           | email, profile info, ssh keys                      | login               |

## Source

- **custom** — module is implemented inside `xsint/modules/`.
- **external** — module wraps a third-party tool or service.

## Auth

- **none** — runs without credentials.
- **api key** — set via `xsint --auth <service> <key>` or the `XSINT_<SERVICE>_API_KEY` env var.
- **setup** — interactive setup via `xsint --auth <service>`.
- **login** — interactive login flow from the upstream tool.

Modules requiring credentials are **disabled by default** — they appear as `locked` in `xsint -m` and are skipped during scans until the relevant `--auth` step has been completed.

See [auth.md](auth.md) for details.

## Status: `active` vs `locked`

A module is `locked` when:

- It declares the input type as `paid` and no API key is configured, or
- It requires a runtime dependency that is not installed (e.g. `ghunt`, `gitfive`), or
- Its `is_ready()` check returns false (e.g. login state missing).

`xsint` skips locked modules during a scan and reports the count under `[*] eligible modules`.
