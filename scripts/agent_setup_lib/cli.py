"""Command-line parsing and orchestration."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path
from typing import Sequence

from .auth_env import AuthEnvironment, auth_env_path, load_auth_environment
from .common import (
    AGENT_COMMANDS,
    REASONING_EFFORTS,
    VERSION,
    Reporter,
    SetupError,
    StateStore,
    build_link_specs,
    normalize_compatibility_argv,
    parse_agents,
    repository_root_from_script,
    require_mutation_environment,
    require_safe_home,
    validate_sources,
)
from .doctor import command_auth_status, command_gitlab_token_status, doctor
from .global_setup import (
    apply_init,
    apply_unlink,
    emit_link_plan,
    emit_unlink_plan,
    plan_init_links,
    plan_unlink,
    recover_pending_transaction,
)
from .project import analyze_project, apply_project
from .public_tools import run_public_tools


def add_common_arguments(parser: argparse.ArgumentParser, *, apply_option: bool = False) -> None:
    parser.add_argument("--agents", required=True, help="Comma-separated agents: codex, claude, gemini, agy")
    parser.add_argument("--home", help="Target Linux home. Defaults to the current user's home.")
    parser.add_argument("--state-dir", help=argparse.SUPPRESS)
    parser.add_argument("--repo-root", help=argparse.SUPPRESS)
    parser.add_argument("--json", action="store_true", help="Emit structured JSON output.")
    parser.add_argument("--allow-root", action="store_true", help=argparse.SUPPRESS)
    if apply_option:
        parser.add_argument("--apply", action="store_true", help="Apply the displayed plan.")


def add_auth_env_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--env-file",
        help="Provider credential file. Defaults to .env in the repository root.",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Set up public tools, shared instructions, and skills on WSL2/Linux."
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    tools_parser = subparsers.add_parser(
        "tools",
        help="Plan or install Firstmate and the public toolchain.",
    )
    tools_mode = tools_parser.add_mutually_exclusive_group()
    tools_mode.add_argument("--apply", action="store_true", help="Install public tools after prerequisites are ready.")
    tools_mode.add_argument(
        "--install",
        action="store_true",
        help="Install missing WSL2 prerequisites, then Firstmate and the public toolchain.",
    )
    tools_parser.add_argument("--firstmate-dir", help="Firstmate checkout. Defaults to ~/agent-tools/firstmate.")
    tools_parser.add_argument("--skip-gnhf", action="store_true", help="Do not install the separate gnhf package.")
    tools_parser.add_argument("--home", help="Target Linux home. Defaults to the current user's home.")
    tools_parser.add_argument("--state-dir", help=argparse.SUPPRESS)
    tools_parser.add_argument("--repo-root", help=argparse.SUPPRESS)
    tools_parser.add_argument("--json", action="store_true", help="Emit structured JSON output.")
    tools_parser.add_argument("--allow-root", action="store_true", help=argparse.SUPPRESS)
    add_auth_env_argument(tools_parser)

    init_parser = subparsers.add_parser("init", help="Plan or create global instruction and skill links.")
    add_common_arguments(init_parser, apply_option=True)
    init_parser.add_argument(
        "--repair",
        action="store_true",
        help="Recreate a missing link that is already recorded as tool-owned.",
    )

    doctor_parser = subparsers.add_parser("doctor", help="Inspect sources, links, state, and local tools without mutation.")
    add_common_arguments(doctor_parser)
    add_auth_env_argument(doctor_parser)

    auth_parser = subparsers.add_parser("auth", help="Validate GitHub and GitLab tokens from the auth env file.")
    add_auth_env_argument(auth_parser)
    auth_parser.add_argument("--repo-root", help=argparse.SUPPRESS)
    auth_parser.add_argument("--json", action="store_true", help="Emit structured JSON output.")

    unlink_parser = subparsers.add_parser("unlink", help="Plan or remove ownership and restore previous setup.")
    add_common_arguments(unlink_parser, apply_option=True)

    project_parser = subparsers.add_parser("project-setup", help="Analyze a project or apply a reviewed proposal.")
    project_parser.add_argument("--apply", action="store_true", help="Apply an existing reviewed proposal.")
    project_parser.add_argument("--proposal-id", help="Proposal ID returned by the analysis phase.")
    project_parser.add_argument("--url", help="HTTPS or SSH Git repository URL for analysis.")
    project_parser.add_argument("--dest", help="Clone destination below --clone-root.")
    project_parser.add_argument("--clone-root", help="Clone root. Defaults to ~/src.")
    project_parser.add_argument("--generator", default="codex", choices=("codex",))
    project_parser.add_argument("--agents", help="Comma-separated target agents for the generated project instructions.")
    project_parser.add_argument("--model", default="gpt-5.6-sol")
    project_parser.add_argument("--effort", choices=REASONING_EFFORTS)
    project_parser.add_argument("--timeout", type=int, default=900, help="Generator timeout in seconds.")
    project_parser.add_argument("--home", help="Target Linux home. Defaults to the current user's home.")
    project_parser.add_argument("--state-dir", help=argparse.SUPPRESS)
    project_parser.add_argument("--repo-root", help=argparse.SUPPRESS)
    project_parser.add_argument("--json", action="store_true")
    project_parser.add_argument("--allow-root", action="store_true", help=argparse.SUPPRESS)

    return parser


def resolve_runtime_paths(args: argparse.Namespace) -> tuple[Path, Path, StateStore]:
    repository_root = (
        Path(args.repo_root).expanduser().resolve(strict=False)
        if getattr(args, "repo_root", None)
        else repository_root_from_script()
    )
    if not repository_root.is_dir():
        raise SetupError("repository_root_missing", f"Repository root does not exist: {repository_root}")
    home = require_safe_home(Path(args.home).expanduser() if getattr(args, "home", None) else Path.home())
    state_dir = Path(args.state_dir).expanduser() if getattr(args, "state_dir", None) else None
    store = StateStore(home, state_dir)
    return repository_root, home, store


def load_command_auth(repository_root: Path, configured: str | None, reporter: Reporter) -> AuthEnvironment:
    auth = load_auth_environment(auth_env_path(repository_root, configured))
    reporter.data["auth_env"] = auth.public_summary()
    configured_providers = [
        name
        for name, enabled in (("github", auth.github_configured), ("gitlab", auth.gitlab_configured))
        if enabled
    ]
    if configured_providers:
        reporter.emit(
            "OK",
            "auth_env",
            f"Loaded credential source for: {', '.join(configured_providers)}.",
        )
    elif auth.present:
        reporter.emit("WARN", "auth_env_empty", f"Auth env has no provider token configured: {auth.path}")
    else:
        reporter.emit("WARN", "auth_env_missing", f"Auth env does not exist: {auth.path}")
    return auth


def validate_auth_environment(
    auth: AuthEnvironment,
    reporter: Reporter,
    *,
    require_all: bool = True,
) -> int:
    missing = []
    if not auth.github_configured:
        missing.append("GH_TOKEN")
    if not auth.gitlab_configured:
        missing.append("GITLAB_TOKEN")
    if missing and require_all:
        raise SetupError("auth_tokens_missing", f"Configure required auth env values: {', '.join(missing)}.")
    environment = auth.command_environment()
    results: dict[str, dict[str, object]] = {}
    if auth.github_configured:
        results["gh"] = command_auth_status("gh", environment=environment, hostname="github.com")
    if auth.gitlab_configured:
        results["glab"] = command_gitlab_token_status(
            environment=environment,
            hostname=auth.gitlab_hostname or "gitlab.com",
        )
    if not results:
        return 0
    reporter.data["authentication"] = results
    failed: list[str] = []
    for name, result in results.items():
        authenticated = bool(result.get("authenticated"))
        reporter.emit(
            "OK" if authenticated else "ERROR",
            "authentication",
            f"{name}: {result.get('status', 'error')}",
        )
        if not authenticated:
            failed.append(name)
    if failed:
        raise SetupError("auth_validation_failed", f"Token validation failed for: {', '.join(failed)}.", exit_code=3)
    reporter.emit("OK", "auth_complete", "GitHub and GitLab tokens are valid for their configured hosts.")
    return 0


def run_command(args: argparse.Namespace, reporter: Reporter) -> int:
    repository_root, home, store = resolve_runtime_paths(args)
    if args.command == "tools":
        auth = load_command_auth(repository_root, args.env_file, reporter)
        mutating = args.apply or args.install
        if mutating:
            require_mutation_environment(allow_root=args.allow_root)
            validate_auth_environment(auth, reporter, require_all=False)
        return run_public_tools(
            home=home,
            configured_firstmate_dir=args.firstmate_dir,
            apply=mutating,
            skip_gnhf=args.skip_gnhf,
            reporter=reporter,
            install_prerequisites=args.install,
            auth_environment=auth.values,
        )
    if args.command == "init":
        agents = parse_agents(args.agents)
        validate_sources(repository_root)
        state, _ = store.load(repository_root)
        specs = build_link_specs(repository_root, home, agents)
        plans = plan_init_links(specs, state, repair=args.repair)
        if not args.apply:
            emit_link_plan(reporter, plans)
            missing_commands = [agent for agent in agents if shutil.which(AGENT_COMMANDS[agent]) is None]
            for agent in missing_commands:
                reporter.emit("WARN", "agent_missing", f"{agent} executable is not installed; configuration can still be planned.")
            if any(plan.conflict for plan in plans):
                raise SetupError("preflight_conflict", "Dry-run found conflicts.")
            reporter.emit("OK", "dry_run", "Dry-run made no filesystem changes.")
            return 0
        require_mutation_environment(allow_root=args.allow_root)
        apply_init(repository_root, home, agents, store, reporter, repair=args.repair)
        return 0
    if args.command == "doctor":
        agents = parse_agents(args.agents)
        auth = load_command_auth(repository_root, args.env_file, reporter)
        return 0 if doctor(repository_root, home, agents, store, reporter, auth_environment=auth) else 2
    if args.command == "auth":
        auth = load_command_auth(repository_root, args.env_file, reporter)
        return validate_auth_environment(auth, reporter)
    if args.command == "unlink":
        agents = parse_agents(args.agents)
        state, _ = store.load(repository_root)
        plans = plan_unlink(state, agents)
        if not args.apply:
            emit_unlink_plan(reporter, plans)
            if any(plan["action"] == "conflict" for plan in plans):
                raise SetupError("unlink_conflict", "Dry-run found unlink conflicts.")
            reporter.emit("OK", "dry_run", "Dry-run made no filesystem changes.")
            return 0
        require_mutation_environment(allow_root=args.allow_root)
        apply_unlink(repository_root, store, agents, reporter)
        return 0
    if args.command == "project-setup":
        require_mutation_environment(allow_root=args.allow_root)
        if args.apply:
            if not args.proposal_id:
                raise SetupError("proposal_id_required", "--proposal-id is required with --apply.")
            if args.url or args.agents:
                raise SetupError(
                    "apply_arguments_refused",
                    "Project apply uses the URL and agents bound to the reviewed proposal; omit --url and --agents.",
                )
            apply_project(args, repository_root, store, reporter)
            return 0
        if args.proposal_id:
            raise SetupError("unexpected_proposal_id", "--proposal-id is only valid with --apply.")
        if not args.url or not args.agents:
            raise SetupError("analysis_arguments_required", "Project analysis requires --url and --agents.")
        if args.timeout < 1 or args.timeout > 86400:
            raise SetupError("invalid_timeout", "--timeout must be between 1 and 86400 seconds.")
        args.agents_parsed = parse_agents(args.agents)
        with store.lock():
            recover_pending_transaction(store, reporter)
        analyze_project(args, repository_root, home, store, reporter)
        return 0
    raise SetupError("unknown_command", f"Unknown command: {args.command}")


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    raw_argv = list(argv) if argv is not None else sys.argv[1:]
    args = parser.parse_args(normalize_compatibility_argv(raw_argv))
    reporter = Reporter(json_mode=bool(getattr(args, "json", False)), command=args.command)
    try:
        exit_code = run_command(args, reporter)
    except SetupError as error:
        reporter.emit("ERROR", error.code, error.message, **error.details)
        reporter.finish(ok=False)
        return error.exit_code
    except KeyboardInterrupt:
        reporter.emit("ERROR", "interrupted", "Operation interrupted by the user.")
        reporter.finish(ok=False)
        return 130
    except Exception as error:  # pragma: no cover - defensive boundary.
        reporter.emit("ERROR", "unexpected_error", f"{type(error).__name__}: {error}")
        reporter.finish(ok=False)
        return 4
    reporter.finish(ok=exit_code == 0)
    return exit_code
