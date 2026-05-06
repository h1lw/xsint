# Usage

## CLI

```text
xsint ( https://github.com/memorypudding/xsint )
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

MISC:
  -h, --help: Print this help summary
```

## Target prefixes

`xsint` auto-detects the target type. When auto-detection is ambiguous (or you want to force a specific type), prefix the target:

| Prefix     | Type      | Example                       |
| ---------- | --------- | ----------------------------- |
| `email:`   | email     | `xsint email:user@example.com` |
| `user:`    | username  | `xsint user:johndoe`          |
| `phone:`   | phone     | `xsint phone:+14155551234`    |
| `ip:`      | ip        | `xsint ip:8.8.8.8`            |
| `addr:`    | address   | `xsint "addr:Tokyo, Japan"`   |
| `hash:`    | hash      | `xsint hash:5f4dcc3b`         |
| `name:`    | name      | `xsint "name:John Doe"`       |
| `id:`      | id        | `xsint id:1234567890`         |
| `ssn:`     | ssn       | `xsint ssn:123-45-6789`       |
| `passport:` | passport | `xsint passport:AB1234567`    |

## Output

By default, `xsint` prints one line per module with its run status:

```text
[+] hibp: ok
[+] nineghz: ok
[+] haxalot_module: ok
[+] email_basic: ok
```

Pass `--show-found` to also print the full findings report after the scan:

```text
[+] hibp: ok
[+] nineghz: ok
[+] haxalot_module: ok
[+] email_basic: ok

type     : EMAIL
findings : 5
sources  : 3

email_basic (1)
  mx records      : mail.example.com

hibp (3)
  Breach          : LinkedIn (2012)
  Breach          : Adobe (2013)
  Paste           : pastebin.com/xyz

nineghz (1)
  Breach          : exampledb (2021)
```

### Module status lines

| Status    | Meaning                                              |
| --------- | ---------------------------------------------------- |
| `ok`      | Module ran and returned results (or none).           |
| `timeout` | Module exceeded `XSINT_MODULE_TIMEOUT` (default 25s). |
| `error`   | Module raised; the error is reported as a finding.   |

## Listing modules

```bash
# All modules
xsint -m

# Modules that handle a specific input type
xsint -m email
xsint -m phone
```

The output shows each module's source (`custom` / `external`), `active`/`locked` status, and supported input types. A module is `locked` when it requires credentials that are not configured.
