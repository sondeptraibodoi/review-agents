"""Read-only diagnostics for agents, links, tools, and Firstmate."""

from __future__ import annotations

import dataclasses
import os
import platform
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any, Sequence

from .auth_env import AuthEnvironment
from .common import (
    AGENT_COMMANDS,
    ROUTED_SKILL_COMMANDS,
    SKILL_SOURCES,
    Reporter,
    SetupError,
    StateStore,
    build_link_specs,
    lexists,
    link_points_to,
    snapshot_path,
    validate_sources,
)
from .repositories import canonical_remote, git_value


VERSION_COMMAND_TIMEOUT_SECONDS = 5
AGENT_VERSION_COMMAND_TIMEOUT_SECONDS = 15
AGENT_VERSION_COMMANDS = frozenset(AGENT_COMMANDS.values())


def command_version(command: str) -> dict[str, Any]:
    executable = shutil.which(command)
    if executable is None:
        return {"status": "missing", "command": command}
    if command == "agy":
        return {
            "status": "ok",
            "command": command,
            "path": executable,
            "version": "presence-only",
        }
    version_arguments = {
        "tmux": ("-V",),
    }.get(command, ("--version",))
    timeout = (
        AGENT_VERSION_COMMAND_TIMEOUT_SECONDS
        if command in AGENT_VERSION_COMMANDS
        else VERSION_COMMAND_TIMEOUT_SECONDS
    )
    try:
        completed = subprocess.run(
            [executable, *version_arguments],
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        return {"status": "error", "command": command, "path": executable, "error": type(error).__name__}
    output = (completed.stdout or completed.stderr).strip().splitlines()
    return {
        "status": "ok" if completed.returncode == 0 else "error",
        "command": command,
        "path": executable,
        "version": output[0][:300] if output else "",
        "returncode": completed.returncode,
    }


def command_auth_status(
    command: str,
    *,
    environment: dict[str, str] | None = None,
    hostname: str | None = None,
) -> dict[str, Any]:
    executable = shutil.which(command)
    if executable is None:
        return {"status": "missing", "command": command, "authenticated": False}
    arguments = [executable, "auth", "status"]
    if hostname:
        arguments.extend(("--hostname", hostname))
    try:
        completed = subprocess.run(
            arguments,
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
            env=environment,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        return {
            "status": "error",
            "command": command,
            "path": executable,
            "authenticated": False,
            "error": type(error).__name__,
        }
    raw_output = (completed.stdout or completed.stderr).strip()
    for key in ("GH_TOKEN", "GITHUB_TOKEN", "GITLAB_TOKEN"):
        sensitive = (environment or {}).get(key)
        if sensitive:
            raw_output = raw_output.replace(sensitive, "<redacted>")
    output = raw_output.splitlines()
    insufficient_scopes = "Missing required token scopes:" in raw_output
    authenticated = completed.returncode == 0 and not insufficient_scopes
    return {
        "status": "ok" if authenticated else ("insufficient-scopes" if insufficient_scopes else "not-authenticated"),
        "command": command,
        "path": executable,
        "authenticated": authenticated,
        "summary": output[0][:300] if output else "",
        "diagnostic": raw_output[:2000],
        "returncode": completed.returncode,
    }


def command_gitlab_token_status(
    *,
    environment: dict[str, str],
    hostname: str,
) -> dict[str, Any]:
    executable = shutil.which("glab")
    if executable is None:
        return {"status": "missing", "command": "glab", "authenticated": False}
    try:
        completed = subprocess.run(
            [executable, "api", "user", "--hostname", hostname, "--silent"],
            check=False,
            capture_output=True,
            text=True,
            timeout=15,
            env=environment,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        return {
            "status": "error",
            "command": "glab",
            "path": executable,
            "authenticated": False,
            "error": type(error).__name__,
        }
    raw_output = (completed.stdout or completed.stderr).strip()
    sensitive = environment.get("GITLAB_TOKEN")
    if sensitive:
        raw_output = raw_output.replace(sensitive, "<redacted>")
    return {
        "status": "ok" if completed.returncode == 0 else "not-authenticated",
        "command": "glab",
        "path": executable,
        "authenticated": completed.returncode == 0,
        "summary": raw_output.splitlines()[0][:300] if raw_output else "",
        "diagnostic": raw_output[:2000],
        "returncode": completed.returncode,
        "validation": "api-user",
    }


def wsl_status() -> dict[str, Any]:
    release = platform.release()
    is_linux = os.name == "posix" and platform.system() == "Linux"
    is_wsl = is_linux and ("microsoft" in release.lower() or "WSL_DISTRO_NAME" in os.environ)
    return {
        "platform": platform.platform(),
        "python": platform.python_version(),
        "is_linux": is_linux,
        "is_wsl": is_wsl,
    }


def inspect_firstmate_checkout(path: Path) -> dict[str, Any]:
    result: dict[str, Any] = {"path": os.fspath(path), "status": "missing"}
    if not (path / ".git").exists():
        return result
    result["status"] = "present"
    result["bootstrap"] = os.fspath(path / "bin/fm-bootstrap.sh")
    result["bootstrap_present"] = (path / "bin/fm-bootstrap.sh").is_file()
    git = shutil.which("git")
    if not git:
        result["git"] = "missing"
        return result
    try:
        origin = git_value(git, path, ["config", "--get", "remote.origin.url"], required=False)
        dirty_output = git_value(git, path, ["status", "--porcelain", "--untracked-files=all"], required=False)
        branch = git_value(git, path, ["branch", "--show-current"], required=False)
        upstream = git_value(
            git,
            path,
            ["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}"],
            required=False,
        )
        ahead = behind = None
        if upstream:
            counts = git_value(
                git,
                path,
                ["rev-list", "--left-right", "--count", f"HEAD...{upstream}"],
                required=False,
            )
            match = re.fullmatch(r"(\d+)\s+(\d+)", counts)
            if match:
                ahead, behind = int(match.group(1)), int(match.group(2))
        try:
            remote_correct = bool(origin) and canonical_remote(origin) == "github.com/kunchenguid/firstmate"
        except SetupError:
            remote_correct = False
        result.update(
            {
                "origin": origin or None,
                "remote_correct": remote_correct,
                "dirty": bool(dirty_output),
                "dirty_entries": len(dirty_output.splitlines()) if dirty_output else 0,
                "branch": branch or None,
                "upstream": upstream or None,
                "ahead": ahead,
                "behind": behind,
                "divergent": bool(ahead and behind),
                "remote_tracking_may_be_stale": True,
            }
        )
    except (OSError, subprocess.TimeoutExpired, SetupError) as error:
        result["inspection_error"] = type(error).__name__
    return result


def inspect_firstmate(home: Path) -> dict[str, Any]:
    return inspect_firstmate_checkout(home / "agent-tools/firstmate")


def duplicate_skill_paths(home: Path, agents: Sequence[str]) -> list[str]:
    duplicates: set[str] = set()
    if "codex" in agents:
        for name in SKILL_SOURCES:
            alternate = home / ".codex/skills" / name / "SKILL.md"
            if lexists(alternate):
                duplicates.add(os.fspath(alternate))
    if "claude" in agents:
        for name in SKILL_SOURCES:
            command = home / ".claude/commands" / f"{name}.md"
            if lexists(command):
                duplicates.add(os.fspath(command))
    return sorted(duplicates)


def doctor(
    repository_root: Path,
    home: Path,
    agents: Sequence[str],
    store: StateStore,
    reporter: Reporter,
    auth_environment: AuthEnvironment | None = None,
) -> bool:
    healthy = True
    reporter.data["environment"] = wsl_status()
    reporter.emit("OK", "environment", f"Python {platform.python_version()} on {platform.platform()}")
    try:
        metadata = validate_sources(repository_root)
        reporter.data["skills"] = {name: dataclasses.asdict(value) for name, value in metadata.items()}
        reporter.emit("OK", "sources", "Global instructions and skill frontmatter are valid.")
    except SetupError as error:
        reporter.emit("ERROR", error.code, error.message)
        healthy = False
    state: dict[str, Any] | None = None
    try:
        state, exists = store.load(repository_root)
        reporter.data["state_file"] = os.fspath(store.state_file)
        reporter.data["state_exists"] = exists
        reporter.emit("OK" if exists else "WARN", "state", "State is valid." if exists else "State has not been created yet.")
    except SetupError as error:
        reporter.emit("ERROR", error.code, error.message)
        healthy = False
    if lexists(store.journal_file):
        reporter.emit("ERROR", "pending_transaction", f"Recovery is required: {store.journal_file}")
        healthy = False
    specs = build_link_specs(repository_root, home, agents)
    links = state["links"] if state else {}
    link_results: list[dict[str, Any]] = []
    for spec in specs:
        current = snapshot_path(spec.destination)
        record = links.get(os.fspath(spec.destination))
        if current["kind"] == "symlink" and link_points_to(spec.destination, spec.source):
            status_value = "managed-ok" if record else "unmanaged-ok"
            level = "OK" if record else "WARN"
        elif current["kind"] == "absent":
            status_value = "missing"
            level = "ERROR"
            healthy = False
        elif current["kind"] == "symlink":
            status_value = "wrong-target"
            level = "ERROR"
            healthy = False
        else:
            status_value = f"conflict-{current['kind']}"
            level = "ERROR"
            healthy = False
        link_results.append(
            {
                "destination": os.fspath(spec.destination),
                "source": os.fspath(spec.source),
                "status": status_value,
                "owners": list(spec.owners),
            }
        )
        reporter.emit(level, "link", f"{spec.destination}: {status_value}")
    reporter.data["links"] = link_results
    versions = {agent: command_version(AGENT_COMMANDS[agent]) for agent in agents}
    reporter.data["agents"] = versions
    for agent, result in versions.items():
        level = "OK" if result["status"] == "ok" else "WARN"
        reporter.emit(level, "agent", f"{agent}: {result['status']}")
    duplicates = duplicate_skill_paths(home, agents)
    reporter.data["duplicate_skill_paths"] = duplicates
    for path in duplicates:
        reporter.emit("WARN", "duplicate_skill", f"Potential duplicate skill entry: {path}")
    tool_names = (
        "git",
        "gh",
        "glab",
        "tmux",
        "node",
        "npm",
        "npx",
        "gnhf",
        "treehouse",
        "no-mistakes",
        "gh-axi",
        "chrome-devtools-axi",
        "lavish-axi",
        "tasks-axi",
        "quota-axi",
    )
    tools = {name: command_version(name) for name in tool_names}
    reporter.data["tools"] = tools
    routed_tools: dict[str, dict[str, Any]] = {}
    for skill_name, command in ROUTED_SKILL_COMMANDS.items():
        result = tools[command]
        routed_tools[skill_name] = result
        available = result["status"] == "ok"
        reporter.emit(
            "OK" if available else "ERROR",
            "routed_tool",
            f"{skill_name}: {command} is {result['status']}.",
        )
        if not available:
            healthy = False
    reporter.data["routed_tools"] = routed_tools
    command_environment = auth_environment.command_environment() if auth_environment else None
    glab_auth = (
        command_gitlab_token_status(
            environment=command_environment,
            hostname=auth_environment.gitlab_hostname or "gitlab.com",
        )
        if auth_environment and auth_environment.gitlab_configured and command_environment
        else command_auth_status(
            "glab",
            environment=command_environment,
            hostname=auth_environment.gitlab_hostname if auth_environment else None,
        )
    )
    auth = {
        "glab": glab_auth,
        "gh": command_auth_status(
            "gh",
            environment=command_environment,
            hostname="github.com",
        ),
    }
    reporter.data["authentication"] = auth
    for name, result in auth.items():
        level = "OK" if result["authenticated"] else "WARN"
        reporter.emit(level, "authentication", f"{name}: {result['status']}")
    firstmate = inspect_firstmate(home)
    reporter.data["firstmate"] = firstmate
    if firstmate["status"] == "missing":
        reporter.emit("WARN", "firstmate", f"Firstmate is not cloned at {firstmate['path']}.")
    else:
        if not firstmate.get("remote_correct"):
            reporter.emit("WARN", "firstmate_remote", "Firstmate origin is not kunchenguid/firstmate.")
        if not firstmate.get("bootstrap_present"):
            reporter.emit("WARN", "firstmate_bootstrap", "Firstmate bootstrap script is missing.")
        if firstmate.get("dirty"):
            reporter.emit(
                "WARN",
                "firstmate_dirty",
                f"Firstmate has {firstmate.get('dirty_entries', 0)} changed or untracked entries.",
            )
        if firstmate.get("divergent"):
            reporter.emit("WARN", "firstmate_divergent", "Firstmate local and upstream histories have diverged.")
        elif firstmate.get("ahead"):
            reporter.emit("WARN", "firstmate_ahead", f"Firstmate is ahead by {firstmate['ahead']} commit(s).")
        elif firstmate.get("behind"):
            reporter.emit("WARN", "firstmate_behind", f"Firstmate is behind by {firstmate['behind']} commit(s).")
    skill_creator = home / ".codex/skills/.system/skill-creator/SKILL.md"
    reporter.data["skill_creator"] = {
        "path": os.fspath(skill_creator),
        "status": "present" if skill_creator.is_file() else "missing",
    }
    chrome_commands = [name for name in ("google-chrome", "chromium", "chromium-browser") if shutil.which(name)]
    reporter.data["chrome"] = {
        "commands": chrome_commands,
        "browser_url_configured": bool(os.environ.get("CHROME_DEVTOOLS_AXI_BROWSER_URL")),
        "status": "available" if chrome_commands or os.environ.get("CHROME_DEVTOOLS_AXI_BROWSER_URL") else "not-configured",
    }
    reporter.emit("OK", "doctor_complete", "Doctor completed without changing the filesystem.")
    return healthy
