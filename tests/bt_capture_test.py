#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only

import subprocess
import sys
from pathlib import Path


def run(*args: str) -> str:
    p = subprocess.run([sys.executable, "tools/bt_capture.py", *args], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return p.stdout.strip()


def test_dry_run_includes_iface_and_output():
    out = run("--dry-run", "--iface", "hci0", "--output", "/tmp/x.btsnoop")
    assert "btmon" in out
    assert "-i hci0" in out
    assert "-w /tmp/x.btsnoop" in out


def test_dry_run_pcapng_adds_editcap_conversion():
    out = run("--dry-run", "--iface", "hci1", "--output", "/tmp/y.pcapng")
    # prints 2 commands, btmon then editcap
    lines = out.splitlines()
    assert len(lines) == 2
    assert lines[0].startswith("btmon ")
    assert "-i hci1" in lines[0]
    assert " -w /tmp/y.btsnoop" in lines[0]
    assert lines[1].startswith("editcap ")
    assert "pcapng" in lines[1]
    assert "/tmp/y.btsnoop" in lines[1]
    assert "/tmp/y.pcapng" in lines[1]


if __name__ == "__main__":
    # tiny runner so this file can be invoked directly without pytest.
    test_dry_run_includes_iface_and_output()
    test_dry_run_pcapng_adds_editcap_conversion()
    print("bt_capture_test: ok")

