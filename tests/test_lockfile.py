"""Tests for lockfile read/write and check."""

import sys, os, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from echolock.tracer import Tracer
from echolock.lockfile import lock, check


def _dummy():
    pass


def test_lock_creates_file():
    tracer = Tracer(scope_modules=["tests.test_lockfile"], ignore_private=False)
    with tracer:
        _dummy()

    with tempfile.NamedTemporaryFile(suffix=".echolock", delete=False) as f:
        path = f.name

    resolved = lock(tracer, path)
    assert resolved.exists()
    content = resolved.read_text()
    assert "fingerprint" in content
    os.unlink(path)


def test_check_passes_when_unchanged():
    tracer = Tracer(scope_modules=["tests.test_lockfile"], ignore_private=False)
    with tracer:
        _dummy()

    with tempfile.NamedTemporaryFile(suffix=".echolock", delete=False) as f:
        path = f.name

    lock(tracer, path)

    # Re-trace the same function
    tracer2 = Tracer(scope_modules=["tests.test_lockfile"], ignore_private=False)
    with tracer2:
        _dummy()

    ok, report = check(tracer2, path)
    assert ok
    assert "✅" in report
    os.unlink(path)
