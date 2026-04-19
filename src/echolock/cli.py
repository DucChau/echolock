"""CLI entrypoint for echolock."""

from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path

from echolock.tracer import Tracer
from echolock.lockfile import lock, check, _read_lockfile
from echolock.diff import diff_report
from echolock.fingerprint import fingerprint


def _resolve_callable(spec: str):
    """Resolve 'module.path:function_name' to a callable."""
    if ":" not in spec:
        print(f"Error: spec must be 'module.path:function_name', got '{spec}'", file=sys.stderr)
        sys.exit(1)

    mod_path, func_name = spec.rsplit(":", 1)
    try:
        mod = importlib.import_module(mod_path)
    except ModuleNotFoundError as e:
        print(f"Error: could not import module '{mod_path}': {e}", file=sys.stderr)
        sys.exit(1)

    fn = getattr(mod, func_name, None)
    if fn is None:
        print(f"Error: '{func_name}' not found in module '{mod_path}'", file=sys.stderr)
        sys.exit(1)
    if not callable(fn):
        print(f"Error: '{mod_path}:{func_name}' is not callable", file=sys.stderr)
        sys.exit(1)

    return mod_path, fn


def _default_lockpath(spec: str) -> str:
    return spec.replace(":", ".").replace(".", "_") + ".echolock"


def cmd_lock(args):
    mod_path, fn = _resolve_callable(args.spec)
    scope = args.scope.split(",") if args.scope else [mod_path.split(".")[0]]

    tracer = Tracer(scope_modules=scope)
    with tracer:
        fn()

    lp = args.output or _default_lockpath(args.spec)
    resolved = lock(tracer, lp, algorithm=args.algorithm)
    n = len(tracer.calls())
    fp = tracer.fingerprint(algorithm=args.algorithm)
    print(f"🔒 Locked {n} calls → {lp} ({args.algorithm}: {fp[:12]}…)")


def cmd_check(args):
    mod_path, fn = _resolve_callable(args.spec)
    scope = args.scope.split(",") if args.scope else [mod_path.split(".")[0]]
    lp = args.lockfile or _default_lockpath(args.spec)

    if not Path(lp).exists():
        print(f"Error: lockfile '{lp}' not found. Run 'echolock lock' first.", file=sys.stderr)
        sys.exit(1)

    tracer = Tracer(scope_modules=scope)
    with tracer:
        fn()

    ok, report = check(tracer, lp)
    print(report)
    sys.exit(0 if ok else 1)


def cmd_trace(args):
    mod_path, fn = _resolve_callable(args.spec)
    scope = args.scope.split(",") if args.scope else [mod_path.split(".")[0]]

    tracer = Tracer(scope_modules=scope)
    with tracer:
        fn()

    calls = tracer.call_names()
    fp = tracer.fingerprint(algorithm=args.algorithm)

    print(f"📡 Traced {len(calls)} calls ({args.algorithm}: {fp[:12]}…)\n")
    for i, name in enumerate(calls, 1):
        print(f"  {i:>4}. {name}")


def cmd_diff(args):
    a = _read_lockfile(args.file_a)
    b = _read_lockfile(args.file_b)
    report = diff_report(
        locked_calls=a.get("calls", []),
        current_calls=b.get("calls", []),
        locked_fp=a.get("fingerprint", ""),
        current_fp=b.get("fingerprint", ""),
    )
    print(report)


def main():
    parser = argparse.ArgumentParser(
        prog="echolock",
        description="Behavioral fingerprinting for Python codebases.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # lock
    p_lock = sub.add_parser("lock", help="Execute a callable and save a lockfile.")
    p_lock.add_argument("spec", help="module.path:function_name")
    p_lock.add_argument("-o", "--output", help="Output lockfile path")
    p_lock.add_argument("-s", "--scope", help="Comma-separated module scopes")
    p_lock.add_argument("-a", "--algorithm", default="sha256", choices=["sha256", "blake2b", "md5"])
    p_lock.set_defaults(func=cmd_lock)

    # check
    p_check = sub.add_parser("check", help="Check a callable against its lockfile.")
    p_check.add_argument("spec", help="module.path:function_name")
    p_check.add_argument("-l", "--lockfile", help="Lockfile path")
    p_check.add_argument("-s", "--scope", help="Comma-separated module scopes")
    p_check.set_defaults(func=cmd_check)

    # trace
    p_trace = sub.add_parser("trace", help="Trace a callable and print the call list.")
    p_trace.add_argument("spec", help="module.path:function_name")
    p_trace.add_argument("-s", "--scope", help="Comma-separated module scopes")
    p_trace.add_argument("-a", "--algorithm", default="sha256", choices=["sha256", "blake2b", "md5"])
    p_trace.set_defaults(func=cmd_trace)

    # diff
    p_diff = sub.add_parser("diff", help="Diff two lockfiles.")
    p_diff.add_argument("file_a", help="First .echolock file")
    p_diff.add_argument("file_b", help="Second .echolock file")
    p_diff.set_defaults(func=cmd_diff)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
