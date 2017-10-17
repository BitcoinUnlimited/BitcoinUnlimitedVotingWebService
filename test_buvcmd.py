import pytest
import buvcmd
import sys

def test1(monkeypatch):
    monkeypatch.setattr("sys.argv", ["", "--help"])

    with pytest.raises(SystemExit):
        buvcmd.buvcmd()

def test2(monkeypatch):
    monkeypatch.setattr("sys.argv", [""])

    with pytest.raises(RuntimeError):
        buvcmd.buvcmd()

def test3(monkeypatch):
    monkeypatch.setattr("sys.argv", ["", "webserver"])

    def f(args):
        raise RuntimeError("Would start webserver")

    monkeypatch.setattr("serve.serve", f)

    with pytest.raises(RuntimeError):
        buvcmd.buvcmd()
