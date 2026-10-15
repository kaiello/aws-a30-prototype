"""Small, dependency-free boundaries for local assets and model destinations."""

import os
import re
import stat
from pathlib import Path
from urllib.parse import unquote, urlsplit


def canonical_endpoint(value: str) -> str:
    """Validate an HTTP API root without changing meaningful path components."""
    if not isinstance(value, str) or not value or re.search(r"[\s\x00-\x1f\x7f\\%]", value):
        raise ValueError("Invalid model endpoint.")
    try:
        parts = urlsplit(value)
        host, port = parts.hostname, parts.port
    except ValueError:
        raise ValueError("Invalid model endpoint.") from None
    if (parts.scheme not in {"https", "http"} or not host or parts.username is not None
            or parts.password is not None or parts.query or parts.fragment or "?" in value or "#" in value
            or any(segment in {".", ".."} for segment in parts.path.split("/"))):
        raise ValueError("Invalid model endpoint.")
    if parts.scheme == "http" and host not in {"localhost", "127.0.0.1", "::1"}:
        raise ValueError("Model endpoints require HTTPS except for configured loopback services.")
    if not host.isascii():
        raise ValueError("Invalid model endpoint.")
    authority = "[" + host + "]" if ":" in host else host.lower()
    if port is not None and port != (443 if parts.scheme == "https" else 80):
        authority += ":" + str(port)
    return parts.scheme + "://" + authority + parts.path.rstrip("/")


def validate_model_endpoint(requested: str | None, configured: str) -> str:
    """A request may select only the endpoint already approved in server config."""
    approved = canonical_endpoint(configured)
    if requested is not None and canonical_endpoint(requested) != approved:
        raise ValueError("Model endpoint is not approved for this engine; configure it on the server.")
    return approved


def canonical_origin(value: str) -> str:
    endpoint = canonical_endpoint(value)
    if urlsplit(endpoint).path:
        raise ValueError("An origin must contain only scheme, host and port.")
    return endpoint


def validate_local_request(headers, server_address, allowed_origins=()) -> str | None:
    """Reject DNS rebinding and unsolicited browser origins; keep JSON CLI access."""
    hosts = headers.get_all("Host", [])
    origins = headers.get_all("Origin", [])
    if len(hosts) != 1 or len(origins) > 1:
        raise ValueError("Invalid request authority.")
    listener, port = server_address[:2]
    valid_hosts = {f"localhost:{port}", f"{listener}:{port}"}
    if listener == "::1":
        valid_hosts = {f"localhost:{port}", f"[::1]:{port}"}
    if hosts[0].lower() not in valid_hosts:
        raise ValueError("Host is not the local listener.")
    current_origin = canonical_origin("http://" + hosts[0])
    approved = {canonical_origin(value) for value in allowed_origins}
    origin = canonical_origin(origins[0]) if origins else None
    if origin is not None and origin != current_origin and origin not in approved:
        raise ValueError("Origin is not approved.")
    if headers.get("Sec-Fetch-Site", "").lower() == "cross-site" and origin not in approved:
        raise ValueError("Cross-site request is not approved.")
    return origin


def decode_asset_name(raw: str) -> str:
    """Decode to closure, then reject Windows aliases, ADS and path syntax."""
    value = raw
    for _ in range(8):
        if re.search(r"%(?![0-9a-fA-F]{2})", value):
            raise ValueError("Invalid asset encoding.")
        decoded = unquote(value, errors="strict")
        if decoded == value:
            break
        value = decoded
    else:
        raise ValueError("Too many asset encodings.")
    if (not value or value in {".", ".."} or value.rstrip(" .") != value
            or any(ord(c) < 32 or c in '/\\:%<>"|?*' for c in value)):
        raise ValueError("Invalid asset name.")
    return value


class AssetStore:
    """Startup allowlist plus containment and file-identity checks on every read."""

    def __init__(self, root: Path, suffixes: set[str]):
        self.root = root.resolve()
        self.allowed_names = frozenset(
            path.name for path in self.root.iterdir()
            if path.suffix.lower() in suffixes and path.is_file() and not path.is_symlink()
        ) if self.root.is_dir() else frozenset()

    def read(self, raw_name: str) -> tuple[str, bytes]:
        name = decode_asset_name(raw_name)
        if name not in self.allowed_names:
            raise FileNotFoundError("Asset is not in the approved catalog.")
        candidate = self.root / name
        if self.root.resolve(strict=True) != self.root:
            raise PermissionError("Asset directory changed.")
        resolved = candidate.resolve(strict=True)
        before = candidate.lstat()
        if (resolved.parent != self.root or candidate.is_symlink()
                or not stat.S_ISREG(before.st_mode) or before.st_nlink != 1):
            raise PermissionError("Asset is not an approved regular file.")
        flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
        with os.fdopen(os.open(candidate, flags), "rb") as stream:
            opened = os.fstat(stream.fileno())
            if ((opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino)
                    or opened.st_nlink != 1 or candidate.resolve(strict=True) != resolved):
                raise PermissionError("Asset changed while opening.")
            return name, stream.read()
