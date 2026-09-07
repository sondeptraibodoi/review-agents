"""Install public tools while delegating Firstmate-owned tools to Firstmate."""

from __future__ import annotations

import dataclasses
import os
import re
import shutil
from pathlib import Path
from typing import Any, Sequence

from .common import Reporter, SetupError, path_is_within, require_safe_home
from .doctor import command_version, inspect_firstmate_checkout
from .repositories import ensure_repository, parse_repository_url, run_checked
from .system_tools import browser_status, install_system_prerequisites


FIRSTMATE_URL = "https://github.com/kunchenguid/firstmate.git"
FIRSTMATE_CANONICAL = "github.com/kunchenguid/firstmate"

# These names come from Firstmate's COMMON_TOOLS and tmux backend requirements.
# We delegate only user-level tools whose upstream installer is suitable for macOS/Linux.
FIRSTMATE_DELEGATED_TOOLS = (
    "no-mistakes",
    "gh-axi",
    "chrome-devtools-axi",
    "lavish-axi",
    "tasks-axi",
    "quota-axi",
    "treehouse",
)
FIRSTMATE_SYSTEM_TOOLS = ("git", "node", "gh", "tmux")
LOCAL_REQUIRED_TOOLS = ("git", "node", "npm", "tmux", "gh")
LOCAL_RECOMMENDED_TOOLS = ("glab", "codex")
MINIMUM_NODE_VERSION = (22, 19, 0)
MINIMUM_NODE_LABEL = "22.19"
WINDOWS_MOUNTED_EXECUTABLE_RE = re.compile(r"^/mnt/[A-Za-z]/")

MISSING_RE = re.compile(r"^MISSING:\s+([A-Za-z0-9._-]+)\b")
MISSING_MANUAL_RE = re.compile(r"^MISSING_MANUAL:\s+([A-Za-z0-9._-]+)\b")
BLOCKING_DIAGNOSTIC_PREFIXES = ("BACKEND_INVALID:", "TANGLE:")


@dataclasses.dataclass(frozen=True)
class BootstrapReport:
    """Structured subset of Firstmate bootstrap detect output."""

    missing: tuple[str, ...]
    manual: tuple[str, ...]
    needs_gh_auth: bool
    output: str
    actionable: tuple[str, ...] = ()


def parse_firstmate_bootstrap_output(output: str) -> BootstrapReport:
    missing: list[str] = []
    manual: list[str] = []
    actionable: list[str] = []
    needs_gh_auth = False
    for raw_line in output.splitlines():
        line = raw_line.strip()
        match = MISSING_RE.match(line)
        if match:
            if match.group(1) not in missing:
                missing.append(match.group(1))
            continue
        manual_match = MISSING_MANUAL_RE.match(line)
        if manual_match:
            if manual_match.group(1) not in manual:
                manual.append(manual_match.group(1))
            continue
        if line.startswith("NEEDS_GH_AUTH"):
            needs_gh_auth = True
            continue
        if line and not line.startswith("BOOTSTRAP_INFO:"):
            actionable.append(line)
    return BootstrapReport(
        missing=tuple(missing),
        manual=tuple(manual),
        needs_gh_auth=needs_gh_auth,
        output=output,
        actionable=tuple(actionable),
    )


def blocking_bootstrap_diagnostics(report: BootstrapReport) -> list[str]:
    return [
        line
        for line in report.actionable
        if line.startswith(BLOCKING_DIAGNOSTIC_PREFIXES)
    ]


def node_version(version: str) -> tuple[int, int, int] | None:
    match = re.search(r"(?:^|\s)v?(\d+)\.(\d+)\.(\d+)(?:\s|$)", version)
    return tuple(int(part) for part in match.groups()) if match else None


def inspect_local_prerequisites() -> dict[str, dict[str, Any]]:
    names = (*LOCAL_REQUIRED_TOOLS, *LOCAL_RECOMMENDED_TOOLS)
    results = {name: command_version(name) for name in names}
    for result in results.values():
        result["native"] = is_native_result(result)
    return results


def is_native_result(result: dict[str, Any]) -> bool:
    path = str(result.get("path", ""))
    return not path or WINDOWS_MOUNTED_EXECUTABLE_RE.match(path) is None


def is_wsl_native_result(result: dict[str, Any]) -> bool:
    """Backward-compatible alias for callers using the old Linux-only name."""

    return is_native_result(result)


def prerequisite_blockers(results: dict[str, dict[str, Any]]) -> list[str]:
    blockers: list[str] = []
    for name in LOCAL_REQUIRED_TOOLS:
        result = results[name]
        if result["status"] != "ok":
            blockers.append(name)
        elif not is_native_result(result):
            blockers.append(f"{name} (native executable required)")
    node = results["node"]
    if node["status"] == "ok":
        version = node_version(str(node.get("version", "")))
        if version is None or version < MINIMUM_NODE_VERSION:
            blockers.append(f"node>={MINIMUM_NODE_LABEL}")
    return blockers


def firstmate_directory(home: Path, configured: str | None) -> Path:
    home = require_safe_home(home)
    selected = Path(configured).expanduser() if configured else home / "agent-tools/firstmate"
    selected = selected.resolve(strict=False)
    if selected == home or not path_is_within(selected, home):
        raise SetupError(
            "unsafe_firstmate_directory",
            f"Firstmate directory must be below the selected home: {selected}",
        )
    return selected


def validate_firstmate_checkout(path: Path, *, executable: bool) -> dict[str, Any]:
    inspection = inspect_firstmate_checkout(path)
    if inspection["status"] != "present":
        raise SetupError("firstmate_missing", f"Firstmate checkout is missing: {path}")
    if not inspection.get("remote_correct"):
        raise SetupError(
            "firstmate_remote_mismatch",
            f"Firstmate origin must be {FIRSTMATE_CANONICAL}: {inspection.get('origin')}",
        )
    if not inspection.get("bootstrap_present"):
        raise SetupError("firstmate_bootstrap_missing", f"Firstmate bootstrap is missing: {path / 'bin/fm-bootstrap.sh'}")
    if executable and inspection.get("dirty"):
        raise SetupError(
            "firstmate_dirty",
            "Refusing to execute a modified Firstmate checkout. Commit, discard, or move its local changes first.",
        )
    if executable and not inspection.get("upstream"):
        raise SetupError(
            "firstmate_upstream_missing",
            "Refusing to execute a Firstmate checkout whose current branch has no tracked upstream.",
        )
    if executable and (inspection.get("ahead") or inspection.get("divergent")):
        raise SetupError(
            "firstmate_unpublished_history",
            "Refusing to execute a Firstmate checkout with local-only or divergent commits.",
        )
    return inspection


def run_firstmate_detect(path: Path, auth_environment: dict[str, str] | None = None) -> BootstrapReport:
    bootstrap = path / "bin/fm-bootstrap.sh"
    bash = shutil.which("bash")
    if bash is None:
        raise SetupError("bash_missing", "bash is required to run Firstmate bootstrap.", exit_code=3)
    environment = dict(os.environ)
    environment.update(auth_environment or {})
    environment["FM_BOOTSTRAP_DETECT_ONLY"] = "1"
    environment["FM_BOOTSTRAP_NETWORK"] = "skip"
    completed = run_checked(
        [bash, os.fspath(bootstrap)],
        cwd=path,
        timeout=120,
        error_code="firstmate_detect_failed",
        env=environment,
    )
    output = "\n".join(part for part in (completed.stdout, completed.stderr) if part)
    return parse_firstmate_bootstrap_output(output)


def classify_firstmate_missing(report: BootstrapReport) -> dict[str, list[str]]:
    delegated = [name for name in FIRSTMATE_DELEGATED_TOOLS if name in report.missing]
    system = [name for name in FIRSTMATE_SYSTEM_TOOLS if name in report.missing]
    known = set(delegated) | set(system)
    unknown = [name for name in report.missing if name not in known]
    return {
        "delegated": delegated,
        "system": system,
        "unknown": unknown,
        "manual": list(report.manual),
    }


def emit_prerequisites(
    reporter: Reporter,
    results: dict[str, dict[str, Any]],
    *,
    install_mode: bool = False,
) -> None:
    for name in LOCAL_REQUIRED_TOOLS:
        result = results[name]
        native = is_native_result(result)
        level = "OK" if result["status"] == "ok" and native else ("PLAN" if install_mode else "ERROR")
        status = result["status"] if native else "non-native-path"
        reporter.emit(level, "tool_prerequisite", f"{name}: {status}")
    for name in LOCAL_RECOMMENDED_TOOLS:
        result = results[name]
        native = is_native_result(result)
        if result["status"] == "ok" and native:
            level = "OK"
        elif install_mode and name == "glab":
            level = "PLAN"
        else:
            level = "WARN"
        status = result["status"] if native else "non-native-path"
        reporter.emit(level, "tool_recommended", f"{name}: {status}")


def emit_firstmate_plan(reporter: Reporter, report: BootstrapReport) -> dict[str, list[str]]:
    classified = classify_firstmate_missing(report)
    reporter.data["firstmate_bootstrap"] = {
        "missing": list(report.missing),
        "delegated": classified["delegated"],
        "system": classified["system"],
        "unknown": classified["unknown"],
        "manual": classified["manual"],
        "needs_gh_auth": report.needs_gh_auth,
        "actionable": list(report.actionable),
    }
    for name in classified["delegated"]:
        reporter.emit("PLAN", "firstmate_install", f"Firstmate bootstrap will install or upgrade {name}.")
    for name in classified["system"]:
        reporter.emit(
            "ERROR",
            "firstmate_system_tool",
            f"Firstmate reports {name} missing; install it as a native system prerequisite before apply.",
        )
    for name in classified["unknown"]:
        reporter.emit(
            "ERROR",
            "firstmate_unknown_tool",
            f"Firstmate requested unsupported backend tool {name}; this setup targets the tmux backend.",
        )
    for name in classified["manual"]:
        reporter.emit("WARN", "firstmate_manual_tool", f"Firstmate requires manual installation for {name}.")
    if not report.missing and not report.manual:
        reporter.emit("OK", "firstmate_dependencies", "Firstmate reports all selected backend tools available.")
    if report.needs_gh_auth:
        reporter.emit("WARN", "github_authentication", "GitHub CLI authentication is still required.")
    blocking = set(blocking_bootstrap_diagnostics(report))
    for line in report.actionable:
        reporter.emit(
            "ERROR" if line in blocking else "WARN",
            "firstmate_diagnostic",
            line,
        )
    return classified


def install_firstmate_delegated(path: Path, tools: Sequence[str]) -> None:
    if not tools:
        return
    bash = shutil.which("bash")
    if bash is None:
        raise SetupError("bash_missing", "bash is required to run Firstmate bootstrap.", exit_code=3)
    run_checked(
        [bash, os.fspath(path / "bin/fm-bootstrap.sh"), "install", *tools],
        cwd=path,
        timeout=1800,
        error_code="firstmate_install_failed",
    )


def install_gnhf(reporter: Reporter) -> None:
    if shutil.which("gnhf"):
        reporter.emit("OK", "gnhf", "gnhf is already installed.")
        return
    npm = shutil.which("npm")
    if npm is None:
        raise SetupError("npm_missing", "npm is required to install gnhf.", exit_code=3)
    run_checked(
        [npm, "install", "-g", "gnhf"],
        timeout=900,
        error_code="gnhf_install_failed",
    )
    if not shutil.which("gnhf"):
        reporter.emit(
            "WARN",
            "gnhf_path",
            "npm completed but gnhf is not on PATH in this shell. Start a new shell and run doctor.",
        )
    else:
        reporter.emit("OK", "gnhf_installed", "Installed gnhf with its official npm package.")


def run_public_tools(
    *,
    home: Path,
    configured_firstmate_dir: str | None,
    apply: bool,
    skip_gnhf: bool,
    reporter: Reporter,
    install_prerequisites: bool = False,
    auth_environment: dict[str, str] | None = None,
) -> int:
    home = require_safe_home(home)
    checkout = firstmate_directory(home, configured_firstmate_dir)
    prerequisites = inspect_local_prerequisites()
    reporter.data["tool_prerequisites_before"] = prerequisites
    emit_prerequisites(reporter, prerequisites, install_mode=install_prerequisites)
    if install_prerequisites:
        install_system_prerequisites(home, prerequisites, reporter)
        prerequisites = inspect_local_prerequisites()
        reporter.data["tool_prerequisites_after"] = prerequisites
        emit_prerequisites(reporter, prerequisites)
    reporter.data["tool_prerequisites"] = prerequisites
    blockers = prerequisite_blockers(prerequisites)
    if blockers:
        raise SetupError(
            "tool_prerequisites_missing",
            f"Install required native prerequisites first: {', '.join(blockers)}.",
            details={
                "required": list(LOCAL_REQUIRED_TOOLS),
                "node_minimum_version": MINIMUM_NODE_LABEL,
            },
        )

    reporter.data["firstmate_directory"] = os.fspath(checkout)
    if not (checkout / ".git").exists():
        reporter.emit("PLAN", "firstmate_clone", f"Clone {FIRSTMATE_URL} to {checkout}.")
        if not apply:
            reporter.data["firstmate_delegated_tools"] = list(FIRSTMATE_DELEGATED_TOOLS)
            for name in FIRSTMATE_DELEGATED_TOOLS:
                reporter.emit(
                    "PLAN",
                    "firstmate_discovery",
                    f"Firstmate will detect whether {name} needs installation after clone.",
                )
            if not skip_gnhf:
                reporter.emit("PLAN", "gnhf_install", "Install gnhf from its official npm package if missing.")
            reporter.emit("OK", "dry_run", "Dry-run made no filesystem changes and did not access the network.")
            return 0
        repository = parse_repository_url(FIRSTMATE_URL)
        ensure_repository(repository, checkout, checkout.parent, reporter)

    inspection = validate_firstmate_checkout(checkout, executable=apply)
    reporter.data["firstmate"] = inspection
    if inspection.get("behind"):
        reporter.emit(
            "WARN",
            "firstmate_behind",
            "The checkout may be behind its tracked upstream because no network fetch is performed during inspection.",
        )

    report = run_firstmate_detect(checkout, auth_environment)
    classified = emit_firstmate_plan(reporter, report)
    if classified["system"] or classified["unknown"] or blocking_bootstrap_diagnostics(report):
        raise SetupError(
            "firstmate_preflight_blocked",
            "Firstmate detection found a system, backend, or checkout issue that must be resolved first.",
        )

    if not apply:
        if not skip_gnhf:
            level = "OK" if shutil.which("gnhf") else "PLAN"
            reporter.emit(level, "gnhf", "gnhf is installed." if level == "OK" else "Install gnhf with npm.")
        reporter.emit("OK", "dry_run", "Dry-run made no filesystem changes and did not access the network.")
        return 0

    install_firstmate_delegated(checkout, classified["delegated"])
    if classified["delegated"]:
        reporter.emit(
            "OK",
            "firstmate_install_complete",
            f"Firstmate bootstrap processed {len(classified['delegated'])} delegated tool(s).",
        )
    if not skip_gnhf:
        install_gnhf(reporter)

    final_report = run_firstmate_detect(checkout, auth_environment)
    final_classified = classify_firstmate_missing(final_report)
    reporter.data["firstmate_bootstrap_after"] = {
        "missing": list(final_report.missing),
        "manual": list(final_report.manual),
    }
    if final_classified["delegated"]:
        raise SetupError(
            "firstmate_install_incomplete",
            f"Firstmate still reports missing delegated tools: {', '.join(final_classified['delegated'])}.",
            exit_code=3,
        )
    if final_classified["system"] or final_classified["unknown"]:
        raise SetupError(
            "firstmate_postcheck_failed",
            "Firstmate post-install check still reports unsupported prerequisites.",
            exit_code=3,
        )
    if blocking_bootstrap_diagnostics(final_report):
        raise SetupError(
            "firstmate_postcheck_diagnostic",
            "Firstmate post-install check reports a blocking backend or checkout diagnostic.",
            exit_code=3,
        )
    for name in final_report.manual:
        reporter.emit("WARN", "firstmate_manual_tool", f"Manual Firstmate dependency remains: {name}.")

    browser = browser_status(home)
    reporter.data["chrome_browser"] = browser
    if browser["available"]:
        reporter.emit("OK", "chrome_browser", "Chrome or a configured browser endpoint is available.")
    else:
        reporter.emit(
            "WARN",
            "chrome_browser",
            "chrome-devtools-axi is installed separately from the Chrome browser; configure a browser when needed.",
        )
    configured_auth = auth_environment or {}
    if configured_auth.get("GH_TOKEN") or configured_auth.get("GITHUB_TOKEN"):
        reporter.emit("OK", "github_auth_source", "GitHub credential source is configured through the auth env file.")
    else:
        reporter.emit("WARN", "github_authentication", "GitHub authentication is not configured in the auth env file.")
    if configured_auth.get("GITLAB_TOKEN"):
        reporter.emit("OK", "gitlab_auth_source", "GitLab credential source is configured through the auth env file.")
    else:
        reporter.emit("WARN", "gitlab_authentication", "GitLab authentication is not configured in the auth env file.")
    reporter.emit("OK", "tools_complete", "Public tool setup completed.")
    return 0
