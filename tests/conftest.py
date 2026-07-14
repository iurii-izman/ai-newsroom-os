from __future__ import annotations

import socket
from collections.abc import Generator

import pytest


@pytest.fixture(autouse=True)
def block_network(monkeypatch: pytest.MonkeyPatch) -> Generator[None]:
    def blocked(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("network access is forbidden in F0 tests")

    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setattr(socket.socket, "connect", blocked)
    yield
