"""Load provider credentials from a non-executable dotenv file."""

from __future__ import annotations

import dataclasses
import os
import re
import urllib.parse
from pathlib import Path

from .common import CONTROL_CHARACTER_RE, SetupError


MAX_AUTH_ENV_BYTES = 64 * 1024
SUPPORTED_AUTH_KEYS = {
    "GH_TOKEN",
    "GITHUB_TOKEN",
    "GITLAB_TOKEN",
    "GITLAB_HOST",
}
TOKEN_KEYS = {"GH_TOKEN", "GITHUB_TOKEN", "GITLAB_TOKEN"}
ASSIGNMENT_RE = re.compile(r"^([A-Z][A-Z0-9_]*)=(.*)$")
PLACEHOLDER_RE = re.compile(r"(?:REPLACE|YOUR[_-]?TOKEN|TOKEN[_-]?HERE|<[^>]+>)", re.IGNORECASE)


@dataclasses.dataclass(frozen=True)
class AuthEnvironment:
    path: Path
    present: bool
    values: dict[str, str] = dataclasses.field(repr=False)

    @property
    def github_configured(self) -> bool:
        return bool(self.values.get("GH_TOKEN") or self.values.get("GITHUB_TOKEN"))

    @property
    def gitlab_configured(self) -> bool:
        return bool(self.values.get("GITLAB_TOKEN"))

    @property
    def gitlab_hostname(self) -> str | None:
        value = self.values.get("GITLAB_HOST")
        return urllib.parse.urlsplit(value).hostname if value else None

    def command_environment(self) -> dict[str, str]:
        environment = dict(os.environ)
        environment.update(self.values)
        return environment

    def public_summary(self) -> dict[str, object]:
        return {
            "path": os.fspath(self.path),
            "present": self.present,
            "configured": {
                "github": self.github_configured,
                "gitlab": self.gitlab_configured,
                "gitlab_host": self.gitlab_hostname,
            },
        }


def auth_env_path(repository_root: Path, configured: str | None) -> Path:
    selected = Path(configured).expanduser() if configured else repository_root / ".env"
    if not selected.is_absolute():
        selected = repository_root / selected
    return selected.resolve(strict=False)


def _dotenv_value(raw_value: str, line_number: int) -> str:
    value = raw_value.strip()
    if not value:
        return ""
    if value[0] in {"'", '"'}:
        if len(value) < 2 or value[-1] != value[0]:
            raise SetupError(
                "auth_env_invalid",
                f"Unclosed quoted value in auth env line {line_number}.",
                exit_code=3,
            )
        value = value[1:-1]
    if CONTROL_CHARACTER_RE.search(value):
        raise SetupError(
            "auth_env_invalid",
            f"Control characters are not allowed in auth env line {line_number}.",
            exit_code=3,
        )
    return value


def _normalize_gitlab_host(value: str) -> str:
    normalized = value if "://" in value else f"https://{value}"
    parsed = urllib.parse.urlsplit(normalized)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
        or parsed.path not in {"", "/"}
    ):
        raise SetupError(
            "gitlab_host_invalid",
            "GITLAB_HOST must be an HTTPS GitLab origin without credentials, path, query, or fragment.",
            exit_code=3,
        )
    port = f":{parsed.port}" if parsed.port else ""
    return f"https://{parsed.hostname.lower()}{port}"


def load_auth_environment(path: Path) -> AuthEnvironment:
    path = path.resolve(strict=False)
    if not path.exists():
        return AuthEnvironment(path=path, present=False, values={})
    if path.is_symlink() or not path.is_file():
        raise SetupError("auth_env_unsafe", f"Auth env must be a regular non-symlink file: {path}", exit_code=3)
    try:
        payload = path.read_bytes()
    except OSError as error:
        raise SetupError("auth_env_read_failed", f"Cannot read auth env: {path}", exit_code=3) from error
    if len(payload) > MAX_AUTH_ENV_BYTES:
        raise SetupError("auth_env_too_large", f"Auth env exceeds 64 KiB: {path}", exit_code=3)
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise SetupError("auth_env_invalid", f"Auth env must be UTF-8: {path}", exit_code=3) from error

    values: dict[str, str] = {}
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        match = ASSIGNMENT_RE.fullmatch(line)
        if not match:
            raise SetupError(
                "auth_env_invalid",
                f"Auth env line {line_number} must use KEY=VALUE syntax.",
                exit_code=3,
            )
        key, raw_value = match.groups()
        if key not in SUPPORTED_AUTH_KEYS:
            raise SetupError(
                "auth_env_key_unsupported",
                f"Unsupported auth env key on line {line_number}: {key}",
                exit_code=3,
            )
        if key in values:
            raise SetupError("auth_env_duplicate", f"Duplicate auth env key: {key}", exit_code=3)
        value = _dotenv_value(raw_value, line_number)
        if value:
            values[key] = value

    if "GH_TOKEN" in values and "GITHUB_TOKEN" in values:
        raise SetupError(
            "github_token_ambiguous",
            "Set only GH_TOKEN or GITHUB_TOKEN, not both.",
            exit_code=3,
        )
    for key in TOKEN_KEYS.intersection(values):
        value = values[key]
        if any(character.isspace() for character in value) or PLACEHOLDER_RE.search(value):
            raise SetupError("auth_token_invalid", f"{key} is empty, contains whitespace, or is still a placeholder.", exit_code=3)
    if "GITLAB_TOKEN" in values:
        if "GITLAB_HOST" not in values:
            raise SetupError("gitlab_host_required", "GITLAB_HOST is required when GITLAB_TOKEN is set.", exit_code=3)
        values["GITLAB_HOST"] = _normalize_gitlab_host(values["GITLAB_HOST"])
    elif "GITLAB_HOST" in values:
        values["GITLAB_HOST"] = _normalize_gitlab_host(values["GITLAB_HOST"])
    return AuthEnvironment(path=path, present=True, values=values)
