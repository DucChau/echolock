"""Tests for the fingerprint module."""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from echolock.fingerprint import fingerprint
import pytest


def test_sha256_deterministic():
    calls = ["mod.a", "mod.b", "mod.c"]
    assert fingerprint(calls) == fingerprint(calls)


def test_different_order_different_hash():
    a = fingerprint(["mod.a", "mod.b"])
    b = fingerprint(["mod.b", "mod.a"])
    assert a != b


def test_blake2b():
    h = fingerprint(["x.y"], algorithm="blake2b")
    assert len(h) == 64  # blake2b with digest_size=32


def test_unsupported_algorithm():
    with pytest.raises(ValueError, match="Unsupported"):
        fingerprint(["x"], algorithm="sha512")


def test_empty_list():
    h = fingerprint([])
    assert isinstance(h, str) and len(h) > 0
