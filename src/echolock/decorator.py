"""Decorator API for echolock tracing."""

from __future__ import annotations

import functools
from pathlib import Path
from typing import Callable, Optional

from echolock.tracer import Tracer
from echolock.lockfile import lock as _lock, check as _check


def trace(
    scope: Optional[list[str]] = None,
    *,
    lockfile: Optional[str] = None,
    algorithm: str = "sha256",
    auto_check: bool = False,
) -> Callable:
    """Decorator that wraps a function with echolock tracing.

    Args:
        scope: Module prefixes to trace (e.g., ["my_app"]).
        lockfile: Optional path to a .echolock file.
                  If provided and the file doesn't exist, it will be created.
                  If it exists and auto_check is True, it will be checked.
        algorithm: Hash algorithm for the fingerprint.
        auto_check: If True and a lockfile exists, raise on drift.

    Returns:
        Decorated function that records calls when executed.
    """

    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            tracer = Tracer(scope_modules=scope)
            with tracer:
                result = fn(*args, **kwargs)

            if lockfile:
                lf = Path(lockfile)
                if not lf.exists():
                    _lock(tracer, lf, algorithm=algorithm)
                elif auto_check:
                    ok, report = _check(tracer, lf, algorithm=algorithm)
                    if not ok:
                        raise RuntimeError(f"echolock drift:\n{report}")

            # Attach trace metadata to the result if possible
            wrapper._last_tracer = tracer  # type: ignore[attr-defined]
            return result

        wrapper._last_tracer = None  # type: ignore[attr-defined]
        return wrapper

    return decorator
