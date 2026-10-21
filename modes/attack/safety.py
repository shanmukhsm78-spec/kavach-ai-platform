"""Scope / safety guard for Attack mode.

THE most important file for a viva: an autonomous pentester must NEVER be
pointed at a site you do not own. Kavach only scans a *local lab*. Before any
request is made we resolve the target hostname to IP addresses and refuse
unless *every* resolved address is loopback or in a private range
(RFC 1918 / RFC 4193). This blocks tricks like a hostname that secretly
resolves to a public server, and "DNS rebinding"-style surprises.
"""
from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse


class ScopeError(Exception):
    """Raised when a target is outside the allowed local-lab scope."""


# Hostnames we always allow (they map to the loopback interface).
_ALWAYS_LOCAL = {"localhost", "localhost.localdomain", "ip6-localhost"}


# Explicit allowlist of "local lab" networks. We deliberately do NOT rely on
# ipaddress.is_private, because that also whitelists ranges we don't want
# (e.g. 198.18.0.0/15 benchmarking, 100.64.0.0/10 CGNAT). Being explicit is
# safer and easier to justify in a viva.
_LOCAL_NETS = [
    ipaddress.ip_network("127.0.0.0/8"),      # IPv4 loopback
    ipaddress.ip_network("10.0.0.0/8"),       # RFC 1918
    ipaddress.ip_network("172.16.0.0/12"),    # RFC 1918
    ipaddress.ip_network("192.168.0.0/16"),   # RFC 1918
    ipaddress.ip_network("169.254.0.0/16"),   # link-local
    ipaddress.ip_network("::1/128"),          # IPv6 loopback
    ipaddress.ip_network("fc00::/7"),         # IPv6 unique-local
    ipaddress.ip_network("fe80::/10"),        # IPv6 link-local
]


def _ip_is_local(ip: str) -> bool:
    """True only if ``ip`` is loopback / RFC1918 / link-local (local lab)."""
    addr = ipaddress.ip_address(ip)
    return any(addr in net for net in _LOCAL_NETS)


def resolve_host_ips(host: str) -> list[str]:
    """Resolve ``host`` to every IP it points at (IPv4 + IPv6)."""
    infos = socket.getaddrinfo(host, None)
    # getaddrinfo returns tuples; the address is the first element of sockaddr.
    return sorted({info[4][0] for info in infos})


def assert_local_target(target_url: str) -> str:
    """Validate ``target_url`` is a local-lab target or raise ScopeError.

    Returns the normalised hostname on success. This is called by the
    pipeline *before* any network traffic is generated.
    """
    parsed = urlparse(target_url)
    if parsed.scheme not in ("http", "https"):
        raise ScopeError(
            f"Only http/https targets are allowed, got scheme '{parsed.scheme}'."
        )
    host = parsed.hostname
    if not host:
        raise ScopeError(f"Could not parse a hostname from '{target_url}'.")

    if host in _ALWAYS_LOCAL:
        return host

    # A literal IP? Check it directly.
    try:
        ipaddress.ip_address(host)
        if _ip_is_local(host):
            return host
        raise ScopeError(
            f"Refusing to scan '{host}': not a loopback/private address. "
            "Kavach only scans a local lab you own."
        )
    except ValueError:
        pass  # not a literal IP, fall through to DNS resolution

    # Resolve the hostname and require *all* answers to be local.
    try:
        ips = resolve_host_ips(host)
    except socket.gaierror as exc:
        raise ScopeError(f"Could not resolve host '{host}': {exc}") from exc

    if not ips:
        raise ScopeError(f"Host '{host}' did not resolve to any address.")

    non_local = [ip for ip in ips if not _ip_is_local(ip)]
    if non_local:
        raise ScopeError(
            f"Refusing to scan '{host}': it resolves to non-local address(es) "
            f"{non_local}. Kavach only scans a local lab you own."
        )
    return host
