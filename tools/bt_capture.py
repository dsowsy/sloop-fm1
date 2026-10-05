#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026
#
# Bluetooth HCI capture helper for Linux/BlueZ.
# Records traffic using btmon's btsnoop output, optionally converting to pcapng via editcap.

from __future__ import annotations

import argparse
import os
import shutil
import signal
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path


def _ts_slug() -> str:
    return time.strftime("%Y%m%d-%H%M%S", time.localtime())


def _which(cmd: str) -> str | None:
    return shutil.which(cmd)


@dataclass(frozen=True)
class Plan:
    btmon_cmd: list[str]
    btmon_out: Path
    final_out: Path
    convert_cmd: list[str] | None


def _plan(output: Path | None, iface: str, duration_s: float | None, force_pcapng: bool) -> Plan:
    out = output
    if out is None:
        out = Path(f"bt-capture-{_ts_slug()}.btsnoop")
    out = out.expanduser()

    want_pcapng = force_pcapng or out.suffix.lower() == ".pcapng"
    if want_pcapng:
        final_out = out if out.suffix.lower() == ".pcapng" else out.with_suffix(".pcapng")
        btmon_out = final_out.with_suffix(".btsnoop")
        convert_cmd = ["editcap", "-F", "pcapng", str(btmon_out), str(final_out)]
    else:
        final_out = out
        btmon_out = out
        convert_cmd = None

    # btmon writes btsnoop. Common invocation:
    #   sudo btmon -i hci0 -w capture.btsnoop
    btmon_cmd = ["btmon", "-i", iface, "-w", str(btmon_out)]

    # duration is enforced by this wrapper (timeout); btmon has no portable "duration" flag.
    _ = duration_s
    return Plan(btmon_cmd=btmon_cmd, btmon_out=btmon_out, final_out=final_out, convert_cmd=convert_cmd)


def _require(cmd: str) -> None:
    if _which(cmd) is None:
        raise SystemExit(
            f"Missing dependency: `{cmd}` not found on PATH.\n"
            f"On Debian/Ubuntu you typically want:\n"
            f"  - `sudo apt-get install bluez` (for btmon)\n"
            f"  - `sudo apt-get install wireshark-common` (for editcap, optional)\n"
        )


def _run(plan: Plan, duration_s: float | None) -> int:
    plan.btmon_out.parent.mkdir(parents=True, exist_ok=True)
    if plan.btmon_out.exists():
        raise SystemExit(f"Refusing to overwrite existing file: {plan.btmon_out}")
    if plan.convert_cmd and plan.final_out.exists():
        raise SystemExit(f"Refusing to overwrite existing file: {plan.final_out}")

    _require("btmon")
    if plan.convert_cmd:
        _require("editcap")

    proc = subprocess.Popen(plan.btmon_cmd)
    try:
        if duration_s is None:
            proc.wait()
        else:
            try:
                proc.wait(timeout=duration_s)
            except subprocess.TimeoutExpired:
                proc.send_signal(signal.SIGINT)
                try:
                    proc.wait(timeout=2.0)
                except subprocess.TimeoutExpired:
                    proc.terminate()
                    proc.wait(timeout=2.0)
    except KeyboardInterrupt:
        proc.send_signal(signal.SIGINT)
        proc.wait(timeout=2.0)

    rc = proc.returncode or 0
    if rc != 0:
        return rc

    if plan.convert_cmd:
        conv = subprocess.run(plan.convert_cmd)
        if conv.returncode != 0:
            return conv.returncode
    return 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(
        description="Capture Bluetooth HCI traffic using btmon (btsnoop), optionally converting to pcapng.",
    )
    ap.add_argument("--iface", default="hci0", help="Bluetooth controller interface (default: hci0)")
    ap.add_argument("-o", "--output", type=Path, default=None, help="Output path (.btsnoop or .pcapng). Default: bt-capture-<ts>.btsnoop")
    ap.add_argument("--pcapng", action="store_true", help="Force pcapng output (requires editcap)")
    ap.add_argument("-d", "--duration", type=float, default=None, help="Stop capture after N seconds (optional)")
    ap.add_argument("--dry-run", action="store_true", help="Print the commands that would run, then exit")
    ns = ap.parse_args(argv)

    plan = _plan(ns.output, ns.iface, ns.duration, ns.pcapng)
    if ns.dry_run:
        print(" ".join(map(str, plan.btmon_cmd)))
        if plan.convert_cmd:
            print(" ".join(map(str, plan.convert_cmd)))
        return 0

    rc = _run(plan, ns.duration)
    if rc == 0:
        # Match the common "tool prints the artifact path" pattern.
        print(plan.final_out)
    return rc


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

