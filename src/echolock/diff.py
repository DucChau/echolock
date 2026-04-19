"""Structural diff engine for call sequences."""

from __future__ import annotations

import difflib


def diff_report(
    locked_calls: list[str],
    current_calls: list[str],
    locked_fp: str,
    current_fp: str,
) -> str:
    """Build a human-readable drift report."""

    lines: list[str] = [
        "❌ Drift detected!",
        "",
        f"   Expected fingerprint: {locked_fp[:16]}…",
        f"   Current fingerprint:  {current_fp[:16]}…",
        "",
    ]

    locked_set = set(locked_calls)
    current_set = set(current_calls)

    added = current_set - locked_set
    removed = locked_set - current_set

    # Position changes for calls present in both
    locked_pos = {name: i for i, name in enumerate(locked_calls)}
    current_pos = {name: i for i, name in enumerate(current_calls)}
    moved = []
    for name in locked_set & current_set:
        if locked_pos[name] != current_pos.get(name):
            moved.append((name, locked_pos[name], current_pos[name]))

    if added:
        lines.append("   Added calls:")
        for name in sorted(added):
            pos = current_calls.index(name)
            lines.append(f"     + {name}  (position {pos})")
        lines.append("")

    if removed:
        lines.append("   Removed calls:")
        for name in sorted(removed):
            pos = locked_calls.index(name)
            lines.append(f"     - {name}  (was position {pos})")
        lines.append("")

    if moved:
        lines.append("   Moved calls:")
        for name, old, new in sorted(moved, key=lambda x: x[2]):
            lines.append(f"     ~ {name}  (position {old} → {new})")
        lines.append("")

    # Unified diff as fallback detail
    differ = difflib.unified_diff(locked_calls, current_calls, lineterm="", fromfile="locked", tofile="current")
    udiff = list(differ)
    if udiff:
        lines.append("   Unified diff:")
        for dl in udiff:
            lines.append(f"     {dl}")

    return "\n".join(lines)
