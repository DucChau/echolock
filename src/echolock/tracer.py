"""Lightweight sys.settrace-based call recorder."""

from __future__ import annotations

import sys
import threading
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CallRecord:
    """A single recorded function call."""
    module: str
    qualname: str
    lineno: int
    position: int

    @property
    def fqn(self) -> str:
        return f"{self.module}.{self.qualname}"


class Tracer:
    """Records an ordered list of function calls scoped to specific modules.

    Usage::

        tracer = Tracer(scope_modules=["my_app"])
        with tracer:
            my_app.pipeline.run(data)
        print(tracer.calls())
    """

    def __init__(
        self,
        scope_modules: Optional[list[str]] = None,
        *,
        ignore_private: bool = True,
    ) -> None:
        self._scope = scope_modules or []
        self._ignore_private = ignore_private
        self._records: list[CallRecord] = []
        self._counter = 0
        self._lock = threading.Lock()
        self._prev_trace = None

    # ── context manager ──────────────────────────────────────────────

    def __enter__(self) -> "Tracer":
        self.start()
        return self

    def __exit__(self, *exc) -> None:
        self.stop()

    def start(self) -> None:
        self._records.clear()
        self._counter = 0
        self._prev_trace = sys.gettrace()
        sys.settrace(self._trace_dispatch)
        threading.settrace(self._trace_dispatch)

    def stop(self) -> None:
        sys.settrace(self._prev_trace)
        threading.settrace(self._prev_trace)  # type: ignore[arg-type]

    # ── tracing callback ─────────────────────────────────────────────

    def _trace_dispatch(self, frame, event, arg):
        if event != "call":
            return self._trace_dispatch

        module = frame.f_globals.get("__name__", "")
        if not self._in_scope(module):
            return self._trace_dispatch

        qualname = frame.f_code.co_qualname if hasattr(frame.f_code, "co_qualname") else frame.f_code.co_name
        if self._ignore_private and qualname.startswith("_"):
            return self._trace_dispatch

        with self._lock:
            self._counter += 1
            rec = CallRecord(
                module=module,
                qualname=qualname,
                lineno=frame.f_lineno,
                position=self._counter,
            )
            self._records.append(rec)

        return self._trace_dispatch

    def _in_scope(self, module: str) -> bool:
        if not self._scope:
            return True
        return any(module == s or module.startswith(s + ".") for s in self._scope)

    # ── public API ───────────────────────────────────────────────────

    def calls(self) -> list[CallRecord]:
        """Return the ordered list of recorded calls."""
        return list(self._records)

    def call_names(self) -> list[str]:
        """Return fully qualified names in call order."""
        return [r.fqn for r in self._records]

    def fingerprint(self, *, algorithm: str = "sha256") -> str:
        """Compute a hex-digest fingerprint of the call sequence."""
        from echolock.fingerprint import fingerprint as _fp
        return _fp(self.call_names(), algorithm=algorithm)

    def reset(self) -> None:
        self._records.clear()
        self._counter = 0
