#!/usr/bin/env python3
# origin: lemoncloud-io/knowledge@45f6b0f:projects/second-brain/config/scripts/vault_verify.py
"""Verify the vault invariants shared by every write lane (ingest, lint, promote).

This is the single post-run check. Skills call it instead of restating the same
assertions in prose:

    python3 projects/second-brain/config/scripts/vault_verify.py --lane ingest \
        --base "$(git merge-base HEAD master)"

Checks (all lanes):
  1. wiki/VAULT_MEMORY.md is under 8 KB (8192 bytes on disk, not decoded length).
  2. No `- Last <Name>:` marker in memory appears more than once (never appended).
  3. Every `- Last <Name>:` line is at most 200 bytes.
  4. raw/ and archive/ are append-only: no modify/delete/rename against the base ref.

Lane check: `--lane ingest|lint|promote` additionally requires that lane's marker
to be present exactly once, so a lane cannot report success without stamping memory.
Omit --lane (or use `--lane none`) for a standalone health check.

Base ref: `--base` defaults to HEAD, which only covers an uncommitted working tree.
Lanes that commit before verifying (ingest commits and opens a PR inside the job)
would see an empty diff and pass vacuously, so every lane call site passes
`--base "$(git merge-base HEAD master)"`. That expression is also correct for a lane
that has not committed yet — on master it resolves to HEAD.

Exit codes: 0 pass, 1 one or more defects, 2 cannot run (vault unresolved, bad usage).
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

MEMORY_REL = "wiki/VAULT_MEMORY.md"
MEMORY_MAX_BYTES = 8192
MARKER_MAX_BYTES = 200
APPEND_ONLY_DIRS = ["raw", "archive"]

LANE_MARKERS = {
    "ingest": "Last Ingest",
    "lint": "Last Lint Pass",
    "promote": "Last Promotion",
}

EXPECTED_DIRS = ["wiki", "raw", "Clippings", "templates"]
MARKER_RE = re.compile(r"^- (Last [^:]+):")


def resolve_vault() -> Path | None:
    """Same contract as vault_ingest_once.py: VAULT_DIR, else cwd, else give up."""
    candidate = Path(os.environ.get("VAULT_DIR") or os.getcwd()).expanduser().resolve()
    if not (candidate / "VAULT_RULES.md").exists():
        return None
    if not all((candidate / d).is_dir() for d in EXPECTED_DIRS):
        return None
    return candidate


def check_memory(vault: Path, lane: str, defects: list[str]) -> None:
    memory = vault / MEMORY_REL
    if not memory.is_file():
        defects.append(f"{MEMORY_REL} is missing")
        return

    size = memory.stat().st_size
    if size >= MEMORY_MAX_BYTES:
        defects.append(f"{MEMORY_REL} is {size} bytes (must stay under {MEMORY_MAX_BYTES})")

    counts: dict[str, int] = {}
    for lineno, raw_line in enumerate(memory.read_text(encoding="utf-8").splitlines(), 1):
        match = MARKER_RE.match(raw_line)
        if not match:
            continue
        name = match.group(1)
        counts[name] = counts.get(name, 0) + 1
        line_bytes = len(raw_line.encode("utf-8"))
        if line_bytes > MARKER_MAX_BYTES:
            defects.append(
                f"{MEMORY_REL}:{lineno} `- {name}:` line is {line_bytes} bytes "
                f"(max {MARKER_MAX_BYTES}); detail belongs in the run-log note"
            )

    for name, count in sorted(counts.items()):
        if count > 1:
            defects.append(
                f"{MEMORY_REL} has {count} `- {name}:` lines; the line is replaced, never appended"
            )

    if lane != "none":
        marker = LANE_MARKERS[lane]
        if counts.get(marker, 0) != 1:
            defects.append(
                f"{MEMORY_REL} has {counts.get(marker, 0)} `- {marker}:` lines "
                f"after a {lane} run (expected exactly 1)"
            )


def check_append_only(vault: Path, base: str, defects: list[str]) -> None:
    existing = [d for d in APPEND_ONLY_DIRS if (vault / d).exists()]
    if not existing:
        return
    try:
        proc = subprocess.run(
            ["git", "diff", "--name-status", base, "--"] + existing,
            cwd=vault,
            capture_output=True,
            text=True,
            timeout=60,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        defects.append(f"append-only check could not run: {exc}")
        return
    if proc.returncode != 0:
        # First stderr line only: git's full usage dump would flood the defect list
        # and push the real defects past the caller's tail truncation.
        stderr_head = proc.stderr.strip().splitlines()[0] if proc.stderr.strip() else "git diff failed"
        defects.append(f"append-only check could not run: {stderr_head}")
        return

    for line in proc.stdout.splitlines():
        if not line.strip():
            continue
        status, _, rest = line.partition("\t")
        if status.startswith("A"):
            continue  # new snapshots are the only legal change
        defects.append(f"append-only violation ({status}): {rest.replace(chr(9), ' -> ')}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify shared vault invariants.")
    parser.add_argument(
        "--lane",
        choices=list(LANE_MARKERS) + ["none"],
        default="none",
        help="lane that just ran; requires its memory marker to be present exactly once",
    )
    parser.add_argument(
        "--base",
        default="HEAD",
        help='git ref the append-only check diffs against; lanes that commit before '
        'verifying must pass "$(git merge-base HEAD master)" (default: HEAD)',
    )
    args = parser.parse_args()
    base = args.base.strip() or "HEAD"

    vault = resolve_vault()
    if vault is None:
        print(
            "vault_verify: cannot resolve the vault root. Set VAULT_DIR or run from a "
            "directory holding VAULT_RULES.md plus " + ", ".join(EXPECTED_DIRS) + "/.",
            file=sys.stderr,
        )
        return 2

    defects: list[str] = []
    check_memory(vault, args.lane, defects)
    check_append_only(vault, base, defects)

    lane_label = args.lane if args.lane != "none" else "shared"
    if defects:
        print(f"FAIL ({lane_label}, base {base}): {len(defects)} defect(s)")
        for defect in defects:
            print(f"  - {defect}")
        return 1

    print(
        f"PASS ({lane_label}, base {base}): memory size, memory markers, "
        "raw/archive append-only"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
