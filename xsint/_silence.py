"""Bulletproof stdout silencer for noisy upstream tools.

Some libraries (alive-progress, colorama in raw mode, anything calling
os.write(1, ...) or termios) bypass sys.stdout patching and write straight
to file descriptor 1. The fd-level redirect here catches those too.

Caveat: this is process-global. While silenced, ANY concurrent coroutine
that writes to stdout in the same event loop is also silenced. Use the
tightest scope possible — wrap only the call that leaks, not the whole
module.
"""
import os
import sys
from contextlib import contextmanager


@contextmanager
def silenced_stdout():
    sys.stdout.flush()
    devnull = os.open(os.devnull, os.O_WRONLY)
    saved = os.dup(1)
    saved_py = sys.stdout
    try:
        os.dup2(devnull, 1)
        sys.stdout = open(os.devnull, "w")
        yield
    finally:
        try:
            sys.stdout.close()
        except Exception:
            pass
        sys.stdout = saved_py
        os.dup2(saved, 1)
        os.close(saved)
        os.close(devnull)
