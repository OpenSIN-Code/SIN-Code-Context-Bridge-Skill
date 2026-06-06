"""Purpose: Tests for the GitNexus context source adapter.

GitNexus is an external CLI; tests stub out `shutil.which` and
`subprocess.run` to simulate available / unavailable / failing / slow
states without ever spawning a real process.

Docs: test_gitnexus_source.doc.md
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

_SKILL_ROOT = Path(__file__).resolve().parent.parent
if str(_SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(_SKILL_ROOT))


def test_gitnexus_unavailable_when_binary_missing(monkeypatch):
    from lib.sources import gitnexus
    monkeypatch.setattr(gitnexus.shutil, "which", lambda _cmd: None)
    src = gitnexus.GitNexusSource()
    assert src.is_available() is False
    assert src.query("anything") == []


def test_gitnexus_query_parses_json(monkeypatch):
    from lib.sources import gitnexus

    monkeypatch.setattr(gitnexus.shutil, "which", lambda _cmd: "/usr/bin/gitnexus")
    payload = {"results": [
        {"symbol": "auth.login", "context": "JWT flow", "score": 0.91, "file": "src/auth.py"},
        {"symbol": "auth.logout", "context": "clear session", "score": 0.5},
    ]}

    class _Proc:
        returncode = 0
        stdout = json.dumps(payload)
        stderr = ""

    monkeypatch.setattr(gitnexus.subprocess, "run",
                        lambda *a, **kw: _Proc())
    out = gitnexus.GitNexusSource().query("auth")
    assert len(out) == 2
    assert out[0].source == "gitnexus"
    assert out[0].score == 0.91
    assert out[0].metadata["file"] == "src/auth.py"


def test_gitnexus_handles_nonzero_exit(monkeypatch):
    from lib.sources import gitnexus

    monkeypatch.setattr(gitnexus.shutil, "which", lambda _cmd: "/usr/bin/gitnexus")

    class _Proc:
        returncode = 2
        stdout = ""
        stderr = "fatal: not a git repo"

    monkeypatch.setattr(gitnexus.subprocess, "run", lambda *a, **kw: _Proc())
    assert gitnexus.GitNexusSource().query("auth") == []


def test_gitnexus_handles_timeout(monkeypatch):
    from lib.sources import gitnexus

    monkeypatch.setattr(gitnexus.shutil, "which", lambda _cmd: "/usr/bin/gitnexus")

    def _hang(*_a, **_kw):
        raise subprocess.TimeoutExpired(cmd="gitnexus", timeout=30)

    monkeypatch.setattr(gitnexus.subprocess, "run", _hang)
    assert gitnexus.GitNexusSource().query("auth") == []


def test_gitnexus_handles_invalid_json(monkeypatch):
    from lib.sources import gitnexus

    monkeypatch.setattr(gitnexus.shutil, "which", lambda _cmd: "/usr/bin/gitnexus")

    class _Proc:
        returncode = 0
        stdout = "not json"
        stderr = ""

    monkeypatch.setattr(gitnexus.subprocess, "run", lambda *a, **kw: _Proc())
    assert gitnexus.GitNexusSource().query("auth") == []
