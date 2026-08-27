"""Safe Git URL parsing, cloning, and repository inspection."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import urllib.parse
import uuid
from pathlib import Path
from typing import Any, Sequence

from .common import (
    CONTROL_CHARACTER_RE,
    RepoURL,
    Reporter,
    SetupError,
    fsync_directory,
    lexists,
    path_is_within,
)


def parse_repository_url(value: str) -> RepoURL:
    if not value or value.startswith("-") or CONTROL_CHARACTER_RE.search(value):
        raise SetupError("invalid_repository_url", "Repository URL is empty or contains unsafe characters.")
    lowered = value.lower()
    if "%2f" in lowered or "%5c" in lowered:
        raise SetupError("invalid_repository_url", "Encoded slash characters are not allowed in repository URLs.")
    host = ""
    path = ""
    if value.startswith("https://") or value.startswith("ssh://"):
        parsed = urllib.parse.urlsplit(value)
        if parsed.scheme not in {"https", "ssh"}:
            raise SetupError("invalid_repository_url", "Only HTTPS and SSH repository URLs are supported.")
        if parsed.password is not None or (parsed.scheme == "https" and parsed.username is not None):
            raise SetupError("repository_credentials_refused", "Credentials must not be embedded in the repository URL.")
        if parsed.query or parsed.fragment or not parsed.hostname:
            raise SetupError("invalid_repository_url", "Repository URL must have a host and no query or fragment.")
        host = parsed.hostname.lower()
        try:
            port = parsed.port
        except ValueError as error:
            raise SetupError("invalid_repository_url", "Repository URL contains an invalid port.") from error
        if port:
            host = f"{host}:{port}"
        path = urllib.parse.unquote(parsed.path).lstrip("/")
    else:
        match = re.fullmatch(
            r"(?P<user>[A-Za-z0-9._-]+)@(?P<host>[A-Za-z0-9._-]+):(?P<path>[^\s]+)",
            value,
        )
        if not match:
            raise SetupError("invalid_repository_url", "Use an HTTPS, ssh://, or user@host:path Git URL.")
        host = match.group("host").lower()
        path = match.group("path")
    path = path.rstrip("/")
    if path.endswith(".git"):
        path = path[:-4]
    segments = path.split("/")
    if len(segments) < 2 or any(segment in {"", ".", ".."} for segment in segments):
        raise SetupError("invalid_repository_path", "Repository URL must include a group and repository name.")
    if any("\\" in segment or CONTROL_CHARACTER_RE.search(segment) for segment in segments):
        raise SetupError("invalid_repository_path", "Repository path contains unsafe characters.")
    canonical = f"{host}/{path}"
    return RepoURL(original=value, host=host, path=path, canonical=canonical)


def safe_destination_component(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", value)
    cleaned = cleaned.strip("._-")
    if not cleaned:
        raise SetupError("invalid_destination_component", f"Cannot derive a safe path from {value!r}")
    return cleaned


def default_clone_destination(clone_root: Path, repository: RepoURL) -> Path:
    result = clone_root / safe_destination_component(repository.host)
    for segment in repository.path.split("/"):
        result /= safe_destination_component(segment)
    return result


def run_checked(
    argv: Sequence[str],
    *,
    cwd: Path | None = None,
    timeout: int = 30,
    error_code: str,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    try:
        completed = subprocess.run(
            list(argv),
            cwd=os.fspath(cwd) if cwd else None,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise SetupError(error_code, f"Command failed to run: {argv[0]}", exit_code=3) from error
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip()[-4000:]
        raise SetupError(
            error_code,
            f"Command failed with exit code {completed.returncode}: {argv[0]}",
            exit_code=3,
            details={"output": detail},
        )
    return completed


def canonical_remote(value: str) -> str:
    return parse_repository_url(value).canonical


def ensure_repository(
    repository: RepoURL,
    destination: Path,
    clone_root: Path,
    reporter: Reporter,
) -> Path:
    git = shutil.which("git")
    if git is None:
        raise SetupError("git_missing", "git is required for project-setup.", exit_code=3)
    clone_root = clone_root.resolve(strict=False)
    destination = destination.resolve(strict=False)
    if not path_is_within(destination, clone_root) or destination == clone_root:
        raise SetupError("unsafe_clone_destination", f"Clone destination must be below {clone_root}: {destination}")
    if destination.exists():
        if not (destination / ".git").exists():
            raise SetupError("not_git_repository", f"Destination is not a Git repository: {destination}")
        remote = run_checked(
            [git, "-C", os.fspath(destination), "config", "--get", "remote.origin.url"],
            error_code="remote_read_failed",
        ).stdout.strip()
        if canonical_remote(remote) != repository.canonical:
            raise SetupError("remote_mismatch", f"Existing repository remote does not match {repository.original}")
        reporter.emit("OK", "repository", f"Using existing clone: {destination}")
        return destination
    clone_root.mkdir(parents=True, exist_ok=True)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.parent / f".{destination.name}.clone-{uuid.uuid4().hex}"
    if lexists(temporary):
        raise SetupError("clone_temporary_exists", f"Temporary clone path already exists: {temporary}")
    try:
        run_checked(
            [git, "clone", "--no-recurse-submodules", "--", repository.original, os.fspath(temporary)],
            timeout=900,
            error_code="clone_failed",
        )
        if lexists(destination):
            raise SetupError("clone_destination_appeared", f"Clone destination appeared during clone: {destination}")
        os.replace(temporary, destination)
        fsync_directory(destination.parent)
    except Exception:
        if temporary.exists() and path_is_within(temporary, clone_root):
            shutil.rmtree(temporary)
        raise
    reporter.emit("OK", "repository_cloned", f"Cloned repository to {destination}")
    return destination


def git_value(git: str, repository: Path, args: Sequence[str], *, required: bool = True) -> str:
    completed = subprocess.run(
        [git, "-C", os.fspath(repository), *args],
        check=False,
        capture_output=True,
        text=True,
        timeout=15,
    )
    if completed.returncode != 0:
        if required:
            raise SetupError("git_inspection_failed", f"git {' '.join(args)} failed.", exit_code=3)
        return ""
    return completed.stdout.strip()


def repository_status(repository: Path) -> dict[str, Any]:
    git = shutil.which("git")
    if git is None:
        raise SetupError("git_missing", "git is required for project-setup.", exit_code=3)
    head = git_value(git, repository, ["rev-parse", "HEAD"])
    dirty_output = git_value(git, repository, ["status", "--porcelain", "--untracked-files=all"])
    upstream = git_value(git, repository, ["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}"], required=False)
    ahead = behind = None
    if upstream:
        counts = git_value(git, repository, ["rev-list", "--left-right", "--count", f"HEAD...{upstream}"], required=False)
        match = re.fullmatch(r"(\d+)\s+(\d+)", counts)
        if match:
            ahead, behind = int(match.group(1)), int(match.group(2))
    return {
        "head": head,
        "dirty": bool(dirty_output),
        "dirty_entries": len(dirty_output.splitlines()) if dirty_output else 0,
        "upstream": upstream or None,
        "ahead": ahead,
        "behind": behind,
        "remote_tracking_may_be_stale": True,
    }
