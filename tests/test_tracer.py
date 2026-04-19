"""Tests for the Tracer engine."""

import sys
import os

# Ensure the src directory is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from echolock.tracer import Tracer


def _helper_a():
    return 1


def _helper_b():
    return _helper_a() + 1


def public_func():
    return _helper_b() + 1


def test_tracer_records_calls():
    tracer = Tracer(scope_modules=["tests.test_tracer"], ignore_private=False)
    with tracer:
        public_func()

    names = tracer.call_names()
    assert len(names) >= 1
    assert any("public_func" in n for n in names)


def test_tracer_ignores_private_by_default():
    tracer = Tracer(scope_modules=["tests.test_tracer"])
    with tracer:
        public_func()

    names = tracer.call_names()
    # _helper_a and _helper_b should be filtered
    assert not any(n.startswith("_") or "._" in n for n in names)


def test_tracer_fingerprint_deterministic():
    tracer = Tracer(scope_modules=["tests.test_tracer"])

    with tracer:
        public_func()
    fp1 = tracer.fingerprint()

    tracer.reset()
    with tracer:
        public_func()
    fp2 = tracer.fingerprint()

    assert fp1 == fp2


def test_tracer_reset():
    tracer = Tracer(scope_modules=["tests.test_tracer"])
    with tracer:
        public_func()
    assert len(tracer.calls()) > 0

    tracer.reset()
    assert len(tracer.calls()) == 0
