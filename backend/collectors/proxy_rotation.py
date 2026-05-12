"""
proxy_rotation.py — Thread-safe proxy rotator with pluggable strategies.

Directly merged from Scrapling (scrapling/engines/toolbelt/proxy_rotation.py).
Provides ProxyRotator, is_proxy_error(), and cyclic_rotation() for use
by collectors and the scrapling adapter.
"""
from __future__ import annotations

from threading import Lock
from typing import Callable

ProxyType = str | dict
RotationStrategy = Callable[[list[ProxyType], int], tuple[ProxyType, int]]

_PROXY_ERROR_INDICATORS = frozenset({
    "net::err_proxy",
    "net::err_tunnel",
    "connection refused",
    "connection reset",
    "connection timed out",
    "failed to connect",
    "could not resolve proxy",
})


def _get_proxy_key(proxy: ProxyType) -> str:
    if isinstance(proxy, str):
        return proxy
    server = proxy.get("server", "")
    username = proxy.get("username", "")
    return f"{server}|{username}"


def is_proxy_error(error: Exception) -> bool:
    error_msg = str(error).lower()
    return any(indicator in error_msg for indicator in _PROXY_ERROR_INDICATORS)


def cyclic_rotation(proxies: list[ProxyType], current_index: int) -> tuple[ProxyType, int]:
    idx = current_index % len(proxies)
    return proxies[idx], (idx + 1) % len(proxies)


class ProxyRotator:
    __slots__ = ("_proxies", "_proxy_to_index", "_strategy", "_current_index", "_lock")

    def __init__(
        self,
        proxies: list[ProxyType],
        strategy: RotationStrategy = cyclic_rotation,
    ):
        if not proxies:
            raise ValueError("At least one proxy must be provided")
        if not callable(strategy):
            raise TypeError(f"strategy must be callable, got {type(strategy).__name__}")

        self._strategy = strategy
        self._lock = Lock()

        self._proxies: list[ProxyType] = []
        self._proxy_to_index: dict[str, int] = {}
        for i, proxy in enumerate(proxies):
            if isinstance(proxy, (str, dict)):
                if isinstance(proxy, dict) and "server" not in proxy:
                    raise ValueError("Proxy dict must have a 'server' key")
                self._proxy_to_index[_get_proxy_key(proxy)] = i
                self._proxies.append(proxy)
            else:
                raise TypeError(f"Invalid proxy type: {type(proxy)}. Expected str or dict.")

        self._current_index = 0

    def get_proxy(self) -> ProxyType:
        with self._lock:
            proxy, self._current_index = self._strategy(self._proxies, self._current_index)
            return proxy

    @property
    def proxies(self) -> list[ProxyType]:
        return list(self._proxies)

    def __len__(self) -> int:
        return len(self._proxies)

    def __repr__(self) -> str:
        return f"ProxyRotator(proxies={len(self._proxies)})"
