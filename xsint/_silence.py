"""Bulletproof stdio silencer for noisy upstream tools.

Some libraries (alive-progress, colorama in raw mode, anything calling
os.write(1, ...) or termios) bypass sys.stdout patching and write straight
to file descriptors 1 / 2. The fd-level redirect here catches those too.

Caveat: this is process-global. While silenced, ANY concurrent coroutine
that writes to stdout/stderr in the same event loop is also silenced. Use
the tightest scope possible — wrap only the call that leaks, not the whole
module.
"""
import os
import sys
from contextlib import contextmanager


@contextmanager
def silenced_stdout():
    sys.stdout.flush()
    sys.stderr.flush()
    devnull = os.open(os.devnull, os.O_WRONLY)
    saved_out = os.dup(1)
    saved_err = os.dup(2)
    saved_py_out = sys.stdout
    saved_py_err = sys.stderr
    try:
        os.dup2(devnull, 1)
        os.dup2(devnull, 2)
        sys.stdout = open(os.devnull, "w")
        sys.stderr = open(os.devnull, "w")
        yield
    finally:
        for s in (sys.stdout, sys.stderr):
            try:
                s.close()
            except Exception:
                pass
        sys.stdout = saved_py_out
        sys.stderr = saved_py_err
        os.dup2(saved_out, 1)
        os.dup2(saved_err, 2)
        os.close(saved_out)
        os.close(saved_err)
        os.close(devnull)
