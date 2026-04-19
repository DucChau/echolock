"""TOML-based .echolock lockfile read/write."""

from __future__ import annotations

import datetime as _dt
import os
from pathlib import Path
from typing import Any

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:
    import tomli as tomllib  # type: ignore[no-redef]

from echolock.tracer import Tracer

# ── helpers ──────────────────────────────────────────────────────────

def _toml_dumps(data: dict[str, Any]) -> str:
    """Minimal TOML serialiser (no third-party dep)."""
    lines: list[str] = []
    for key, value in data.items():
        if isinstance(value, list):
            items = ", ".join(f'"{v}"' for v in value)
            lines.append(f"{key} = [{items}]")
        elif isinstance(value, str):
            lines.append(f'{key} = "{value}"')
        elif isinstance(value, int):
            lines.append(f"{key} = {value}")
        elif isinstance(value, bool):
            lines.append(f"{key} = {'true' if value else 'false'}")
        else:
            lines.append(f'{key} = "{value}"')
    return "\n".join(lines) + "\n"


# ── public API ───────────────────────────────────────────────────────

def lock(tracer: Tracer, path: str | Path = "echolock.lock", *, algorithm: str = "sha256") -> Path:
    """Write a lockfile from the tracer's current state.

    Returns the resolved Path of the written file.
    """
    path = Path(path)
    names = tracer.call_names()
    fp = tracer.fingerprint(algorithm=algorithm)

    data = {
        "echolock_version": "0.1.0",
        "algorithm": algorithm,
        "fingerprint": fp,
        "num_calls": len(names),
        "locked_at": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "calls": names,
    }

    path.write_text(_toml_dumps(data), encoding="utf-8")
    return path.resolve()


def _read_lockfile(path: str | Path) -> dict[str, Any]:
    raw = Path(path).read_bytes()
    return tomllib.loads(raw.decode("utf-8"))


def check(tracer: Tracer, path: str | Path = "echolock.lock", *, algorithm: str | None = None) -> tuple[bool, str]:
    """Compare the tracer's current fingerprint against a lockfile.

    Returns:
        (ok, report) — ok is True when fingerprints match.
    """
    from echolock.diff import diff_report  # avoid circular

    locked = _read_lockfile(path)
    algo = algorithm or locked.get("algorithm", "sha256")
    current_fp = tracer.fingerprint(algorithm=algo)
    locked_fp = locked.get("fingerprint", "")

    if current_fp == locked_fp:
        return True, f"✅ Fingerprint matches ({algo}: {current_fp[:12]}…)"

    report = diff_report(
        locked_calls=locked.get("calls", []),
        current_calls=tracer.call_names(),
        locked_fp=locked_fp,
        current_fp=current_fp,
    )
    return False, report
