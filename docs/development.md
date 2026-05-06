# Writing a Module

Each module is a single Python file under `xsint/modules/`. The engine discovers modules by scanning that directory and parsing each file's top-level `INFO` dict via AST — no import is needed for `xsint -m` to list capabilities, so listing stays fast even when third-party deps are missing.

## Minimal module

```python
# xsint/modules/myservice.py
import aiohttp

INFO = {
    "free":    ["email"],          # types runnable without credentials
    "paid":    ["phone"],          # types that require api_key
    "api_key": "myservice",        # optional; resolved via XSINT_MYSERVICE_API_KEY / config.json
    "returns": ["breaches"],
}


async def run(session: aiohttp.ClientSession, target: str):
    # session has the user's proxy already wired in
    async with session.get(f"https://api.example.com/lookup/{target}") as resp:
        data = await resp.json()

    findings = [
        {
            "label":  "Breach",
            "value":  hit["name"],
            "source": "myservice",
        }
        for hit in data.get("hits", [])
    ]
    return 1, findings
```

## INFO fields

| Key       | Type             | Required | Notes                                                                 |
| --------- | ---------------- | -------- | --------------------------------------------------------------------- |
| `free`    | `list[str]`      | yes      | Input types this module handles without credentials.                  |
| `paid`    | `list[str]`      | no       | Input types that need an API key.                                     |
| `api_key` | `str`            | no       | Service name for credential lookup. Required if `paid` is non-empty.  |
| `returns` | `list[str]`      | yes      | Free-form list of what this module produces. Surfaced in module info. |
| `themes`  | `dict[str, dict]` | no      | Reserved for source labelling.                                        |

Valid input types: `email`, `username`, `phone`, `ip`, `address`, `hash`, `name`, `id`, `ssn`, `passport`.

## `run()` contract

```python
async def run(session: aiohttp.ClientSession, target: str) -> tuple[int, list[dict]]:
    ...
```

- `session` — shared `aiohttp.ClientSession` with the user's proxy applied. Reuse it; do not create your own.
- `target` — the cleaned target string (prefix already stripped).
- Return value — `(status_code, findings)`. `status_code` is informational. `findings` is a list of dicts.

### Finding shape

```python
{
    "label":  str,    # short tag, left-aligned in the report
    "value":  str,    # the actual data point
    "source": str,    # usually the module's display name
    "group":  str,    # optional; renders as "<group> / <label>"
}
```

Findings with `value == "None found"` are filtered out by the engine, so modules can return a sentinel row when they want to be transparent about a no-op.

## Optional hooks

### `is_ready()`

Return `True` (or a `(True, "")` tuple) when the module is configured and runnable. Return `False` (or `(False, "reason")`) to mark the module locked. Used for `ghunt`, `gitfive`, `haxalot` to gate on login state.

```python
def is_ready():
    if not _has_login():
        return False, "run xsint --auth myservice"
    return True, ""
```

### `setup()`

An async function invoked by `xsint --auth <service>` for `SETUP_SERVICES`. Used by `haxalot_module`.

```python
async def setup():
    # interactive flow; persist whatever the module needs
    ...
```

To register your module as a setup-style service, add its name to `SETUP_SERVICES` in [xsint/__main__.py](../xsint/__main__.py).

## Timeouts

Every module is wrapped in `asyncio.wait_for` with a per-module timeout (default 25s, override with `XSINT_MODULE_TIMEOUT`). A timeout becomes a `medium`-risk finding rather than an exception — design your HTTP calls to respect the budget.

## Errors

Uncaught exceptions are converted to findings labelled `Error`. The scan continues with the rest of the modules.
