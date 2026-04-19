"""echolock — behavioral fingerprinting for Python codebases."""

from echolock.tracer import Tracer
from echolock.fingerprint import fingerprint
from echolock.lockfile import lock, check
from echolock.decorator import trace

__all__ = ["Tracer", "fingerprint", "lock", "check", "trace"]
__version__ = "0.1.0"
