"""Shared types, validation, path handling, and state persistence."""

from __future__ import annotations

import contextlib
import dataclasses
import datetime as dt
import errno
import hashlib
import json
import os
import platform
import re
import stat
import uuid
from pathlib import Path
from typing import Any, Callable, Iterator, Sequence

try:
    import fcntl
except ImportError:  # pragma: no cover - unavailable on the supported target only.
    fcntl = None


VERSION = "0.4.0"
STATE_SCHEMA_VERSION = 1
OUTPUT_SCHEMA_VERSION = 1
SUPPORTED_AGENTS = ("codex", "claude", "gemini", "agy")
AGENT_ALIASES = {
    "antigravity": "agy",
    "antigravity-cli": "agy",
}
AGENT_COMMANDS = {
    "codex": "codex",
    "claude": "claude",
    "gemini": "gemini",
    "agy": "agy",
}
SKILL_SOURCES = {
    "tuln-opinions": Path("skills/OPINIONS.md"),
    "python-tools": Path("skills/PYTHON.md"),
    "lavish": Path("skills/LAVISH.md"),
    "chrome-devtools-axi": Path("skills/CHROME_DEVTOOLS_AXI.md"),
}
ROUTED_SKILL_COMMANDS = {
    "lavish": "lavish-axi",
    "chrome-devtools-axi": "chrome-devtools-axi",
}
REASONING_EFFORTS = ("none", "low", "medium", "high", "xhigh", "max")
MAX_PROPOSAL_BYTES = 64 * 1024
MAX_ARCHIVE_BYTES = 1024 * 1024 * 1024
REQUIRED_PROPOSAL_HEADINGS = (
    "# Project Agent Instructions",
    "## Project purpose",
    "## Repository layout",
    "## Primary entrypoints",
    "## Build and run commands",
    "## Verification commands",
    "## Architecture and ownership boundaries",
    "## GitLab workflow and CI",
    "## Generated and protected files",
    "## Security constraints",
    "## Known unknowns",
    "## Verification evidence",
)
STRONG_SECRET_PATTERNS = (
    re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bgh[opsu]_[A-Za-z0-9]{30,}\b"),
    re.compile(r"\bglpat-[A-Za-z0-9_-]{16,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
)
CONTROL_CHARACTER_RE = re.compile(r"[\x00-\x1f\x7f]")
SAFE_PROPOSAL_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,127}$")
SAFE_MODEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
SKILL_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
CLOCK: Callable[[], dt.datetime] = lambda: dt.datetime.now(dt.timezone.utc)


class SetupError(RuntimeError):
    """A user-facing error with a stable code and process exit code."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        exit_code: int = 2,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.exit_code = exit_code
        self.details = details or {}


@dataclasses.dataclass(frozen=True)
class SkillMetadata:
    name: str
    description: str


@dataclasses.dataclass(frozen=True)
class LinkSpec:
    destination: Path
    source: Path
    kind: str
    owners: tuple[str, ...]
    skill_name: str | None = None


@dataclasses.dataclass
class PlannedLink:
    spec: LinkSpec
    action: str
    snapshot: dict[str, Any]
    record: dict[str, Any] | None
    message: str
    conflict: bool = False
    backup_path: Path | None = None


@dataclasses.dataclass(frozen=True)
class RepoURL:
    original: str
    host: str
    path: str
    canonical: str

    @property
    def repo_name(self) -> str:
        return self.path.rsplit("/", 1)[-1]


class Reporter:
    """Collect structured events and optionally render human-readable output."""

    def __init__(self, *, json_mode: bool, command: str) -> None:
        self.json_mode = json_mode
        self.command = command
        self.events: list[dict[str, Any]] = []
        self.data: dict[str, Any] = {}

    def emit(
        self,
        level: str,
        code: str,
        message: str,
        **details: Any,
    ) -> None:
        event = {
            "level": level,
            "code": code,
            "message": message,
        }
        if details:
            event["details"] = details
        self.events.append(event)
        if not self.json_mode:
            print(f"{level:<5} {code}: {message}")

    def finish(self, *, ok: bool) -> None:
        if self.json_mode:
            payload = {
                "schema_version": OUTPUT_SCHEMA_VERSION,
                "tool_version": VERSION,
                "command": self.command,
                "ok": ok,
                "events": self.events,
                "data": self.data,
            }
            print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))


def utc_now() -> dt.datetime:
    value = CLOCK()
    if value.tzinfo is None:
        value = value.replace(tzinfo=dt.timezone.utc)
    return value.astimezone(dt.timezone.utc)


def utc_iso() -> str:
    return utc_now().isoformat().replace("+00:00", "Z")


def transaction_id(prefix: str) -> str:
    stamp = utc_now().strftime("%Y%m%dT%H%M%S%fZ")
    return f"{prefix}-{stamp}-{uuid.uuid4().hex[:8]}"


def lexists(path: Path) -> bool:
    return os.path.lexists(os.fspath(path))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def path_is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve(strict=False).relative_to(root.resolve(strict=False))
        return True
    except ValueError:
        return False


def destination_parent_is_within(path: Path, root: Path) -> bool:
    try:
        path.parent.resolve(strict=False).relative_to(root.resolve(strict=False))
        return True
    except ValueError:
        return False


def require_safe_home(home: Path) -> Path:
    resolved = home.expanduser().resolve(strict=False)
    if not resolved.is_absolute() or resolved == Path("/"):
        raise SetupError("unsafe_home", f"Refusing unsafe home path: {resolved}")
    return resolved


def require_mutation_environment(*, allow_root: bool) -> None:
    system = platform.system()
    if os.name != "posix" or system not in {"Darwin", "Linux"}:
        raise SetupError(
            "unsupported_platform",
            "Mutating commands require macOS or Linux with python3.",
        )
    if hasattr(os, "geteuid") and os.geteuid() == 0 and not allow_root:
        raise SetupError(
            "root_refused",
            "Refusing to mutate a root profile. Run as the intended user or pass --allow-root explicitly.",
        )


def repository_root_from_script() -> Path:
    return Path(__file__).resolve().parents[2]


def parse_agents(raw: str) -> tuple[str, ...]:
    values: list[str] = []
    unknown: list[str] = []
    for item in raw.split(","):
        normalized = item.strip().lower()
        if not normalized:
            continue
        normalized = AGENT_ALIASES.get(normalized, normalized)
        if normalized not in SUPPORTED_AGENTS:
            unknown.append(item.strip())
            continue
        if normalized not in values:
            values.append(normalized)
    if unknown:
        raise SetupError(
            "unknown_agent",
            f"Unsupported agent value(s): {', '.join(unknown)}",
            details={"supported": list(SUPPORTED_AGENTS)},
        )
    if not values:
        raise SetupError("missing_agent", "At least one supported agent is required.")
    return tuple(values)


def normalize_model_and_effort(model: str, effort: str | None) -> tuple[str, str]:
    combined_effort: str | None = None
    normalized_model = model
    for candidate in sorted(REASONING_EFFORTS, key=len, reverse=True):
        marker = f"_{candidate}"
        if model.endswith(marker) and len(model) > len(marker):
            normalized_model = model[: -len(marker)]
            combined_effort = candidate
            break
    if combined_effort and effort and combined_effort != effort:
        raise SetupError(
            "reasoning_effort_conflict",
            f"Model suffix requests {combined_effort}, but --effort requests {effort}.",
        )
    return normalized_model, effort or combined_effort or "xhigh"


def normalize_compatibility_argv(argv: Sequence[str]) -> list[str]:
    values = list(argv)
    if not values:
        return values
    first = values[0]
    if first.startswith("--init="):
        agents = first.split("=", 1)[1]
        return ["init", "--agents", agents, *values[1:]]
    for prefix in ("--project_setup=", "--project-setup="):
        if first.startswith(prefix):
            repository_url = first.split("=", 1)[1]
            return ["project-setup", "--url", repository_url, *values[1:]]
    return values


def parse_frontmatter(path: Path) -> SkillMetadata:
    if not path.is_file() or path.is_symlink():
        raise SetupError("invalid_skill_source", f"Skill source must be a regular file: {path}")
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as error:
        raise SetupError("invalid_utf8", f"Skill source is not valid UTF-8: {path}") from error
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise SetupError("missing_frontmatter", f"Skill source has no YAML frontmatter: {path}")
    closing = None
    for index in range(1, min(len(lines), 64)):
        if lines[index].strip() == "---":
            closing = index
            break
    if closing is None:
        raise SetupError("invalid_frontmatter", f"Skill frontmatter is not closed: {path}")
    values: dict[str, str] = {}
    for line in lines[1:closing]:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if ":" not in stripped:
            raise SetupError("invalid_frontmatter", f"Unsupported frontmatter line in {path}: {line}")
        key, value = stripped.split(":", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    name = values.get("name", "")
    description = values.get("description", "")
    if not SKILL_NAME_RE.fullmatch(name):
        raise SetupError("invalid_skill_name", f"Invalid skill name in {path}: {name!r}")
    if not description:
        raise SetupError("missing_skill_description", f"Skill description is empty: {path}")
    return SkillMetadata(name=name, description=description)


def validate_sources(repository_root: Path) -> dict[str, SkillMetadata]:
    root = repository_root.resolve(strict=True)
    global_source = root / "global/AGENTS.md"
    if not global_source.is_file() or global_source.is_symlink():
        raise SetupError(
            "missing_global_source",
            f"Global instruction source must be a regular file: {global_source}",
        )
    try:
        global_text = global_source.read_text(encoding="utf-8")
    except UnicodeDecodeError as error:
        raise SetupError("invalid_utf8", f"Global instruction source is not valid UTF-8: {global_source}") from error
    if "\x00" in global_text:
        raise SetupError("invalid_global_source", f"Global instruction source contains a NUL byte: {global_source}")
    metadata: dict[str, SkillMetadata] = {}
    for expected_name, relative in SKILL_SOURCES.items():
        source = root / relative
        if not path_is_within(source, root):
            raise SetupError("source_outside_repository", f"Source escapes repository root: {source}")
        parsed = parse_frontmatter(source)
        if parsed.name != expected_name:
            raise SetupError(
                "skill_name_mismatch",
                f"Expected skill name {expected_name!r}, found {parsed.name!r} in {source}",
            )
        metadata[expected_name] = parsed
    return metadata


def instruction_destination(home: Path, agent: str) -> Path:
    mapping = {
        "codex": home / ".codex/AGENTS.md",
        "claude": home / ".claude/CLAUDE.md",
        "gemini": home / ".gemini/GEMINI.md",
        "agy": home / ".gemini/GEMINI.md",
    }
    return mapping[agent]


def skill_destination(home: Path, agent: str, skill_name: str) -> Path:
    if agent == "codex":
        return home / ".agents/skills" / skill_name / "SKILL.md"
    if agent == "claude":
        return home / ".claude/skills" / skill_name / "SKILL.md"
    if agent == "gemini":
        return home / ".gemini/skills" / skill_name / "SKILL.md"
    if agent == "agy":
        return home / ".gemini/antigravity-cli/skills" / skill_name / "SKILL.md"
    raise SetupError("unknown_agent", f"No skill destination mapping for {agent}")


def build_link_specs(
    repository_root: Path,
    home: Path,
    agents: Sequence[str],
) -> list[LinkSpec]:
    root = repository_root.resolve(strict=True)
    home = require_safe_home(home)
    raw_specs: list[LinkSpec] = []
    for agent in agents:
        raw_specs.append(
            LinkSpec(
                destination=instruction_destination(home, agent),
                source=root / "global/AGENTS.md",
                kind="instruction",
                owners=(agent,),
            )
        )
        for skill_name, relative in SKILL_SOURCES.items():
            raw_specs.append(
                LinkSpec(
                    destination=skill_destination(home, agent, skill_name),
                    source=root / relative,
                    kind="skill",
                    owners=(agent,),
                    skill_name=skill_name,
                )
            )
    merged: dict[str, LinkSpec] = {}
    for spec in raw_specs:
        if not destination_parent_is_within(spec.destination, home):
            raise SetupError(
                "destination_outside_home",
                f"Destination escapes selected home: {spec.destination}",
            )
        key = os.path.normpath(os.fspath(spec.destination))
        previous = merged.get(key)
        if previous is None:
            merged[key] = spec
            continue
        if previous.source.resolve() != spec.source.resolve() or previous.kind != spec.kind:
            raise SetupError(
                "destination_collision",
                f"Multiple sources map to the same destination: {spec.destination}",
            )
        owners = tuple(agent for agent in SUPPORTED_AGENTS if agent in set(previous.owners + spec.owners))
        merged[key] = dataclasses.replace(previous, owners=owners)
    return sorted(merged.values(), key=lambda item: os.fspath(item.destination))


def snapshot_path(path: Path) -> dict[str, Any]:
    if not lexists(path):
        return {"kind": "absent"}
    info = path.lstat()
    if stat.S_ISLNK(info.st_mode):
        return {
            "kind": "symlink",
            "link_target": os.readlink(path),
        }
    if stat.S_ISREG(info.st_mode):
        return {
            "kind": "file",
            "sha256": sha256_file(path),
            "mode": stat.S_IMODE(info.st_mode),
            "size": info.st_size,
        }
    if stat.S_ISDIR(info.st_mode):
        return {"kind": "directory"}
    return {"kind": "special", "mode": info.st_mode}


def snapshot_matches(path: Path, snapshot: dict[str, Any]) -> bool:
    current = snapshot_path(path)
    if current.get("kind") != snapshot.get("kind"):
        return False
    kind = snapshot.get("kind")
    if kind == "file":
        return current.get("sha256") == snapshot.get("sha256")
    if kind == "symlink":
        return current.get("link_target") == snapshot.get("link_target")
    return kind in {"absent", "directory", "special"}


def normalized_link_target(destination: Path) -> Path | None:
    if not destination.is_symlink():
        return None
    raw = Path(os.readlink(destination))
    if not raw.is_absolute():
        raw = destination.parent / raw
    return Path(os.path.realpath(raw))


def link_points_to(destination: Path, source: Path) -> bool:
    target = normalized_link_target(destination)
    if target is None:
        return False
    return os.path.normcase(os.fspath(target)) == os.path.normcase(
        os.fspath(Path(os.path.realpath(source)))
    )


def new_state(repository_root: Path) -> dict[str, Any]:
    now = utc_iso()
    return {
        "schema_version": STATE_SCHEMA_VERSION,
        "repository_root": os.fspath(repository_root.resolve(strict=False)),
        "links": {},
        "created_at": now,
        "updated_at": now,
    }


def validate_state(state: Any) -> dict[str, Any]:
    if not isinstance(state, dict):
        raise SetupError("invalid_state", "State root must be a JSON object.")
    schema = state.get("schema_version")
    if schema != STATE_SCHEMA_VERSION:
        raise SetupError(
            "unsupported_state_schema",
            f"Expected state schema {STATE_SCHEMA_VERSION}, found {schema!r}.",
        )
    links = state.get("links")
    if not isinstance(links, dict):
        raise SetupError("invalid_state", "State links must be a JSON object.")
    for destination, record in links.items():
        if not isinstance(destination, str) or not os.path.isabs(destination):
            raise SetupError("invalid_state", f"Invalid state destination: {destination!r}")
        if not isinstance(record, dict):
            raise SetupError("invalid_state", f"Invalid state record for {destination}")
        if record.get("destination") != destination:
            raise SetupError("invalid_state", f"State destination mismatch for {destination}")
        source = record.get("source")
        if not isinstance(source, str) or not os.path.isabs(source):
            raise SetupError("invalid_state", f"Invalid source in state for {destination}")
        owners = record.get("owners")
        if not isinstance(owners, list) or any(owner not in SUPPORTED_AGENTS for owner in owners):
            raise SetupError("invalid_state", f"Invalid owners in state for {destination}")
        if len(set(owners)) != len(owners):
            raise SetupError("invalid_state", f"Duplicate owners in state for {destination}")
        if not isinstance(record.get("owned"), bool):
            raise SetupError("invalid_state", f"Invalid owned flag in state for {destination}")
    return state


class StateStore:
    """State, lock, backup, and crash-recovery journal management."""

    def __init__(self, home: Path, state_dir: Path | None = None) -> None:
        home = require_safe_home(home)
        self.home = home
        selected = state_dir or home / ".local/state/agent-advance-setup"
        self.directory = selected.expanduser().resolve(strict=False)
        if not path_is_within(self.directory, home):
            raise SetupError("state_outside_home", f"State directory escapes selected home: {self.directory}")
        self.state_file = self.directory / "state.json"
        self.journal_file = self.directory / "pending-transaction.json"
        self.lock_file = self.directory / "setup.lock"
        self.backup_directory = self.directory / "backups"
        self.projects_directory = self.directory / "projects"

    def load(self, repository_root: Path) -> tuple[dict[str, Any], bool]:
        if not lexists(self.state_file):
            return new_state(repository_root), False
        if self.state_file.is_symlink() or not self.state_file.is_file():
            raise SetupError("invalid_state", f"State path must be a regular file: {self.state_file}")
        try:
            payload = json.loads(self.state_file.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise SetupError("invalid_state", f"Cannot read state file: {self.state_file}") from error
        return validate_state(payload), True

    @contextlib.contextmanager
    def lock(self) -> Iterator[None]:
        if fcntl is None:
            raise SetupError("locking_unavailable", "fcntl locking is required on macOS/Linux.")
        self.directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(self.directory, 0o700)
        descriptor = os.open(self.lock_file, os.O_RDWR | os.O_CREAT, 0o600)
        try:
            os.chmod(self.lock_file, 0o600)
            fcntl.flock(descriptor, fcntl.LOCK_EX)
            yield
        finally:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
            os.close(descriptor)

    def _atomic_write_json(self, path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        if path_is_within(path.parent, self.directory):
            os.chmod(path.parent, 0o700)
        temporary = path.parent / f".{path.name}.{uuid.uuid4().hex}.tmp"
        descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
                json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
            os.chmod(path, 0o600)
            fsync_directory(path.parent)
        except Exception:
            if lexists(temporary):
                temporary.unlink()
            raise

    def save_state(self, state: dict[str, Any]) -> None:
        state["updated_at"] = utc_iso()
        self._atomic_write_json(self.state_file, validate_state(state))

    def write_journal(self, journal: dict[str, Any]) -> None:
        self._atomic_write_json(self.journal_file, journal)

    def load_journal(self) -> dict[str, Any] | None:
        if not lexists(self.journal_file):
            return None
        if self.journal_file.is_symlink() or not self.journal_file.is_file():
            raise SetupError("invalid_journal", f"Journal must be a regular file: {self.journal_file}")
        try:
            payload = json.loads(self.journal_file.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise SetupError("invalid_journal", f"Cannot read journal: {self.journal_file}") from error
        if not isinstance(payload, dict) or payload.get("schema_version") != 1:
            raise SetupError("invalid_journal", f"Unsupported journal format: {self.journal_file}")
        return payload

    def clear_journal(self) -> None:
        if lexists(self.journal_file):
            self.journal_file.unlink()
            fsync_directory(self.directory)


def fsync_directory(path: Path) -> None:
    try:
        descriptor = os.open(path, os.O_RDONLY)
    except OSError:
        return
    try:
        try:
            os.fsync(descriptor)
        except OSError as error:
            unsupported_errors = {errno.EINVAL, errno.ENOTSUP, errno.EOPNOTSUPP}
            if platform.system() != "Darwin" or error.errno not in unsupported_errors:
                raise
    finally:
        os.close(descriptor)
