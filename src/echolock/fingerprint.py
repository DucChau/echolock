"""Hashing utilities for call sequences."""

from __future__ import annotations

import hashlib


_SUPPORTED = {"sha256", "blake2b", "md5"}


def fingerprint(call_names: list[str], *, algorithm: str = "sha256") -> str:
    """Compute a deterministic hex-digest for an ordered call list.

    Args:
        call_names: Fully-qualified function names in call order.
        algorithm: One of 'sha256', 'blake2b', 'md5'.

    Returns:
        Hex-encoded hash string.
    """
    if algorithm not in _SUPPORTED:
        raise ValueError(f"Unsupported algorithm {algorithm!r}. Choose from {_SUPPORTED}")

    canonical = "\n".join(call_names).encode("utf-8")

    if algorithm == "blake2b":
        h = hashlib.blake2b(canonical, digest_size=32)
    else:
        h = hashlib.new(algorithm, canonical)

    return h.hexdigest()
