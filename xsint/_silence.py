"""Targeted upstream-print silencer.

Process-global stdio redirection (dup2 fd 1) silences the noisy library
but also swallows xsint's own concurrent status prints from other modules
that finish during the wrapped window. Instead, we patch `print` and
`Console` references in specific upstream modules' namespaces — silences
only their output, leaves everyone else's prints untouched.
"""
import importlib
import sys


_NOOP = lambda *args, **kwargs: None


def silence_module_prints(module_names):
    """Replace `print` in each module's namespace with a no-op.

    Idempotent: safe to call once at xsint startup. Affects only
    `module.print(...)` resolution in those modules — does not touch
    builtins.print or any other module's bindings.
    """
    for name in module_names:
        try:
            mod = importlib.import_module(name)
        except Exception:
            continue
        mod.print = _NOOP


def quiet_rich_console(console):
    """Mute a rich.Console instance in-place by sending it to /dev/null."""
    import os
    null_file = open(os.devnull, "w")
    console.file = null_file

