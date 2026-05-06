# Authentication

Some modules require credentials. The `--auth` subcommand handles all three styles:

| Style         | Modules                  | How it's stored                                        |
| ------------- | ------------------------ | ------------------------------------------------------ |
| API key       | `hibp`, `intelx`, `9ghz` | `config.json` or `XSINT_<SERVICE>_API_KEY` env var      |
| Interactive login | `ghunt`, `gitfive`   | Delegated to the upstream tool's own login flow         |
| Interactive setup | `haxalot`            | Module-managed (writes its own state)                   |

## Status

```bash
xsint --auth
```

Prints a table of every gated module, whether credentials are set, where they came from, and a hint if not.

## API key modules

```bash
xsint --auth hibp YOUR_HIBP_KEY
xsint --auth intelx YOUR_INTELX_KEY
xsint --auth 9ghz YOUR_9GHZ_KEY
```

The key is written to `config.json` in the current working directory.

### Resolution order

When a module reads its key, `xsint` checks:

1. `XSINT_<SERVICE>_API_KEY` environment variable
2. `<service>_key` field in `config.json`

Set the env var to override a stored key without editing the config:

```bash
export XSINT_HIBP_API_KEY=abcd1234
```

## Login modules

```bash
xsint --auth ghunt
xsint --auth gitfive
```

These shell out to the upstream tool's `login` command (e.g. `ghunt login`). `xsint` tries, in order:

1. `python -m <service> login` (or, for `gitfive`, the package's CLI parser directly — gitfive has no `__main__`).
2. A binary in the same directory as `sys.executable`.
3. Whatever `<service>` resolves to on `PATH`.
4. `~/.local/pipx/venvs/<service>/bin/<service>`.

If the login tool runs but exits non-zero, `xsint` reports the failure and suggests retrying. If it never runs, `xsint` tells you to install the upstream package.

## Setup modules

```bash
xsint --auth haxalot
```

Runs the module's own `setup()` coroutine. State is module-internal; check the module source for details.

## Where credentials live

- `./config.json` — written by `xsint --auth <api_service> <key>`. Plain JSON, edit by hand if needed.
- Upstream tool config dirs — e.g. `~/.malfrats/ghunt/`, `~/.gitfive/`. Managed by those tools, not `xsint`.
