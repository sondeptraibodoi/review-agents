"""Transactional global instruction and skill link management."""

from __future__ import annotations

import os
import re
import shutil
import uuid
from pathlib import Path
from typing import Any, Sequence

from .common import (
    LinkSpec,
    PlannedLink,
    Reporter,
    SetupError,
    StateStore,
    SUPPORTED_AGENTS,
    build_link_specs,
    fsync_directory,
    lexists,
    link_points_to,
    sha256_file,
    snapshot_matches,
    snapshot_path,
    transaction_id,
    utc_iso,
    utc_now,
)


def ensure_directories(paths: Sequence[Path]) -> list[Path]:
    created: list[Path] = []
    for path in sorted(set(paths), key=lambda item: len(item.parts)):
        missing: list[Path] = []
        cursor = path
        while not cursor.exists():
            missing.append(cursor)
            if cursor.parent == cursor:
                break
            cursor = cursor.parent
        for item in reversed(missing):
            item.mkdir()
            created.append(item)
    return created


def missing_directory_paths(paths: Sequence[Path]) -> list[Path]:
    missing: set[Path] = set()
    for path in paths:
        cursor = path
        while not lexists(cursor):
            missing.add(cursor)
            if cursor.parent == cursor:
                break
            cursor = cursor.parent
    return sorted(missing, key=lambda item: len(item.parts), reverse=True)


def remove_empty_directories(paths: Sequence[Path]) -> None:
    for path in sorted(set(paths), key=lambda item: len(item.parts), reverse=True):
        try:
            path.rmdir()
        except OSError:
            pass


def unique_adjacent_backup(destination: Path, reserved: set[str]) -> Path:
    suffix = destination.suffix
    stem = destination.name[: -len(suffix)] if suffix else destination.name
    first = destination.with_name(f"{stem}-bak{suffix}")
    candidates = [first]
    stamp = utc_now().strftime("%Y%m%dT%H%M%S%fZ")
    candidates.append(destination.with_name(f"{stem}-bak-{stamp}{suffix}"))
    for index in range(2, 10000):
        candidates.append(destination.with_name(f"{stem}-bak-{stamp}-{index}{suffix}"))
        if len(candidates) > 8:
            break
    for candidate in candidates:
        key = os.path.normpath(os.fspath(candidate))
        if key not in reserved and not lexists(candidate):
            reserved.add(key)
            return candidate
    random_candidate = destination.with_name(f"{stem}-bak-{stamp}-{uuid.uuid4().hex[:8]}{suffix}")
    key = os.path.normpath(os.fspath(random_candidate))
    if key in reserved or lexists(random_candidate):
        raise SetupError("backup_collision", f"Cannot allocate backup path for {destination}")
    reserved.add(key)
    return random_candidate


def backup_path_for(
    planned: PlannedLink,
    store: StateStore,
    tx_id: str,
    reserved: set[str],
) -> Path:
    if planned.spec.kind == "instruction":
        return unique_adjacent_backup(planned.spec.destination, reserved)
    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", planned.spec.destination.name)
    candidate = store.backup_directory / tx_id / f"{planned.spec.skill_name}-{safe_name}"
    key = os.path.normpath(os.fspath(candidate))
    if key in reserved or lexists(candidate):
        candidate = candidate.with_name(f"{candidate.name}-{uuid.uuid4().hex[:8]}")
        key = os.path.normpath(os.fspath(candidate))
    reserved.add(key)
    return candidate


def copy_regular_exclusive(source: Path, destination: Path, mode: int) -> None:
    descriptor = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
    try:
        with source.open("rb") as input_handle, os.fdopen(descriptor, "wb") as output_handle:
            shutil.copyfileobj(input_handle, output_handle, length=1024 * 1024)
            output_handle.flush()
            os.fsync(output_handle.fileno())
        shutil.copystat(source, destination, follow_symlinks=False)
    except Exception:
        if lexists(destination):
            destination.unlink()
        raise


def create_backup(planned: PlannedLink) -> dict[str, Any]:
    if planned.backup_path is None:
        raise SetupError("internal_error", "Backup path was not assigned.", exit_code=4)
    destination = planned.spec.destination
    backup = planned.backup_path
    snapshot = planned.snapshot
    if not snapshot_matches(destination, snapshot):
        raise SetupError("destination_changed", f"Destination changed during setup: {destination}")
    if lexists(backup):
        raise SetupError("backup_exists", f"Refusing to overwrite backup: {backup}")
    backup.parent.mkdir(parents=True, exist_ok=True)
    if snapshot["kind"] == "file":
        copy_regular_exclusive(destination, backup, int(snapshot["mode"]))
        original_hash = sha256_file(destination)
        backup_hash = sha256_file(backup)
        if original_hash != snapshot["sha256"] or backup_hash != snapshot["sha256"]:
            raise SetupError("backup_hash_mismatch", f"Backup verification failed for {destination}")
        result = {
            "kind": "file",
            "backup_path": os.fspath(backup),
            "sha256": backup_hash,
            "mode": int(snapshot["mode"]),
        }
    elif snapshot["kind"] == "symlink":
        raw_target = str(snapshot["link_target"])
        os.symlink(raw_target, backup)
        if os.readlink(backup) != raw_target:
            raise SetupError("backup_link_mismatch", f"Symlink backup verification failed for {destination}")
        result = {
            "kind": "symlink",
            "backup_path": os.fspath(backup),
            "link_target": raw_target,
        }
    else:
        raise SetupError("invalid_backup_source", f"Cannot back up {snapshot['kind']}: {destination}")
    fsync_directory(backup.parent)
    return result


def temporary_sibling(destination: Path) -> Path:
    for _ in range(32):
        candidate = destination.parent / f".{destination.name}.agent-setup-{uuid.uuid4().hex}.tmp"
        if not lexists(candidate):
            return candidate
    raise SetupError("temporary_name_collision", f"Cannot allocate temporary path beside {destination}")


def replace_with_symlink(destination: Path, source: Path, *, expected: dict[str, Any]) -> None:
    if not snapshot_matches(destination, expected):
        raise SetupError("destination_changed", f"Destination changed during setup: {destination}")
    temporary = temporary_sibling(destination)
    os.symlink(os.fspath(source), temporary)
    try:
        os.replace(temporary, destination)
        fsync_directory(destination.parent)
    finally:
        if lexists(temporary):
            temporary.unlink()


def create_symlink_exclusive(destination: Path, source: Path) -> None:
    os.symlink(os.fspath(source), destination)
    fsync_directory(destination.parent)


def make_link_record(
    planned: PlannedLink,
    *,
    previous: dict[str, Any],
    owned: bool,
) -> dict[str, Any]:
    return {
        "destination": os.fspath(planned.spec.destination),
        "source": os.fspath(planned.spec.source),
        "kind": planned.spec.kind,
        "skill_name": planned.spec.skill_name,
        "owners": list(planned.spec.owners),
        "owned": owned,
        "previous": previous,
        "installed_at": utc_iso(),
        "updated_at": utc_iso(),
    }


def merge_owners(existing: Sequence[str], requested: Sequence[str]) -> list[str]:
    combined = set(existing) | set(requested)
    return [agent for agent in SUPPORTED_AGENTS if agent in combined]


def plan_init_links(
    specs: Sequence[LinkSpec],
    state: dict[str, Any],
    *,
    repair: bool,
) -> list[PlannedLink]:
    plans: list[PlannedLink] = []
    links: dict[str, dict[str, Any]] = state["links"]
    for spec in specs:
        destination_key = os.fspath(spec.destination)
        record = links.get(destination_key)
        current = snapshot_path(spec.destination)
        if record is not None:
            recorded_source = Path(record["source"])
            if recorded_source != spec.source:
                plans.append(
                    PlannedLink(
                        spec,
                        "conflict",
                        current,
                        record,
                        "State points to a different source checkout; automatic migration is refused.",
                        True,
                    )
                )
                continue
            if current["kind"] == "symlink" and link_points_to(spec.destination, recorded_source):
                owners = merge_owners(record["owners"], spec.owners)
                action = "owner-update" if owners != record["owners"] else "ok"
                message = "Managed symlink is correct."
                if action == "owner-update":
                    message = "Managed symlink is correct and will add shared owners."
                plans.append(PlannedLink(spec, action, current, record, message))
                continue
            if current["kind"] == "absent" and record.get("owned") and repair:
                plans.append(PlannedLink(spec, "repair", current, record, "Managed symlink is missing and will be repaired."))
                continue
            plans.append(
                PlannedLink(
                    spec,
                    "conflict",
                    current,
                    record,
                    "A previously managed destination was changed outside this tool.",
                    True,
                )
            )
            continue
        if current["kind"] in {"directory", "special"}:
            plans.append(
                PlannedLink(
                    spec,
                    "conflict",
                    current,
                    None,
                    f"Destination is a {current['kind']} and will not be replaced.",
                    True,
                )
            )
        elif current["kind"] == "absent":
            plans.append(PlannedLink(spec, "create", current, None, "Symlink will be created."))
        elif current["kind"] == "symlink" and link_points_to(spec.destination, spec.source):
            plans.append(
                PlannedLink(
                    spec,
                    "adopt",
                    current,
                    None,
                    "Existing correct symlink will be recorded as pre-existing and will not be removed by unlink.",
                )
            )
        else:
            plans.append(PlannedLink(spec, "replace", current, None, "Existing destination will be backed up and replaced."))
    return plans


def emit_link_plan(reporter: Reporter, plans: Sequence[PlannedLink]) -> None:
    level_for = {
        "ok": "OK",
        "owner-update": "PLAN",
        "create": "PLAN",
        "replace": "PLAN",
        "repair": "PLAN",
        "adopt": "PLAN",
        "conflict": "ERROR",
    }
    for planned in plans:
        reporter.emit(
            level_for[planned.action],
            planned.action,
            f"{planned.spec.destination}: {planned.message}",
            destination=os.fspath(planned.spec.destination),
            source=os.fspath(planned.spec.source),
            owners=list(planned.spec.owners),
            kind=planned.spec.kind,
        )


def journal_action(planned: PlannedLink) -> dict[str, Any]:
    return {
        "action": planned.action,
        "destination": os.fspath(planned.spec.destination),
        "source": os.fspath(planned.spec.source),
        "snapshot": planned.snapshot,
        "backup_path": os.fspath(planned.backup_path) if planned.backup_path else None,
    }


def atomic_restore_regular(destination: Path, backup: Path, expected_hash: str, mode: int) -> None:
    if backup.is_symlink() or not backup.is_file() or sha256_file(backup) != expected_hash:
        raise SetupError("backup_invalid", f"Backup is missing or changed: {backup}", exit_code=4)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = temporary_sibling(destination)
    copy_regular_exclusive(backup, temporary, mode)
    try:
        os.replace(temporary, destination)
        fsync_directory(destination.parent)
    finally:
        if lexists(temporary):
            temporary.unlink()


def atomic_restore_symlink(destination: Path, raw_target: str) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = temporary_sibling(destination)
    os.symlink(raw_target, temporary)
    try:
        os.replace(temporary, destination)
        fsync_directory(destination.parent)
    finally:
        if lexists(temporary):
            temporary.unlink()


def previous_from_record(record: dict[str, Any]) -> dict[str, Any]:
    previous = record.get("previous")
    if not isinstance(previous, dict) or previous.get("kind") not in {"absent", "file", "symlink"}:
        raise SetupError("invalid_state", f"Invalid previous value for {record.get('destination')}")
    return previous


def restore_previous(destination: Path, previous: dict[str, Any]) -> None:
    kind = previous["kind"]
    if kind == "absent":
        if lexists(destination):
            destination.unlink()
            fsync_directory(destination.parent)
        return
    if kind == "file":
        atomic_restore_regular(
            destination,
            Path(previous["backup_path"]),
            str(previous["sha256"]),
            int(previous["mode"]),
        )
        return
    if kind == "symlink":
        backup = Path(previous["backup_path"])
        expected_target = str(previous["link_target"])
        if not backup.is_symlink() or os.readlink(backup) != expected_target:
            raise SetupError("backup_invalid", f"Symlink backup is missing or changed: {backup}", exit_code=4)
        atomic_restore_symlink(destination, expected_target)
        return
    raise SetupError("invalid_state", f"Unsupported previous kind: {kind}")


def recover_init_transaction(store: StateStore, journal: dict[str, Any], reporter: Reporter) -> None:
    for action in reversed(journal.get("actions", [])):
        if action.get("action") not in {"create", "replace", "repair"}:
            continue
        destination = Path(action["destination"])
        source = Path(action["source"])
        original = action["snapshot"]
        current = snapshot_path(destination)
        if snapshot_matches(destination, original):
            continue
        if not (current["kind"] == "absent" or link_points_to(destination, source)):
            raise SetupError(
                "recovery_conflict",
                f"Cannot safely recover changed destination: {destination}",
                exit_code=4,
            )
        if original["kind"] == "absent":
            if lexists(destination):
                destination.unlink()
        elif original["kind"] == "file":
            backup_path = action.get("backup_path")
            if not backup_path:
                raise SetupError("recovery_missing_backup", f"Missing backup for {destination}", exit_code=4)
            atomic_restore_regular(
                destination,
                Path(backup_path),
                str(original["sha256"]),
                int(original["mode"]),
            )
        elif original["kind"] == "symlink":
            atomic_restore_symlink(destination, str(original["link_target"]))
        else:
            raise SetupError("recovery_unsupported", f"Cannot recover {destination}", exit_code=4)
    remove_empty_directories([Path(item) for item in journal.get("created_directories", [])])
    if journal.get("state_existed"):
        store.save_state(journal["before_state"])
    elif lexists(store.state_file):
        store.state_file.unlink()
    store.clear_journal()
    reporter.emit("WARN", "transaction_recovered", "Recovered an interrupted init transaction.")


def recover_unlink_transaction(store: StateStore, journal: dict[str, Any], reporter: Reporter) -> None:
    for action in reversed(journal.get("actions", [])):
        if action.get("filesystem_action") is not True:
            continue
        destination = Path(action["destination"])
        source = Path(action["source"])
        if link_points_to(destination, source):
            continue
        previous = action.get("previous", {"kind": "absent"})
        current = snapshot_path(destination)
        matches_restored = False
        if previous["kind"] == "absent":
            matches_restored = current["kind"] == "absent"
        elif previous["kind"] == "file":
            matches_restored = current["kind"] == "file" and current.get("sha256") == previous.get("sha256")
        elif previous["kind"] == "symlink":
            matches_restored = current["kind"] == "symlink" and current.get("link_target") == previous.get("link_target")
        if not matches_restored:
            raise SetupError(
                "recovery_conflict",
                f"Cannot safely recover interrupted unlink for {destination}",
                exit_code=4,
            )
        destination.parent.mkdir(parents=True, exist_ok=True)
        if current["kind"] == "absent":
            create_symlink_exclusive(destination, source)
        else:
            replace_with_symlink(destination, source, expected=current)
    if journal.get("state_existed"):
        store.save_state(journal["before_state"])
    store.clear_journal()
    reporter.emit("WARN", "transaction_recovered", "Recovered an interrupted unlink transaction.")


def recover_project_transaction(store: StateStore, journal: dict[str, Any], reporter: Reporter) -> None:
    import json

    metadata_path = Path(journal["metadata_path"])
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        metadata = {}
    if metadata.get("applied_at"):
        for action in journal.get("actions", []):
            destination = Path(action["destination"])
            current = snapshot_path(destination)
            if action["kind"] == "file":
                matches = current["kind"] == "file" and current.get("sha256") == action["sha256"]
            else:
                matches = current["kind"] == "symlink" and current.get("link_target") == action["link_target"]
            if not matches:
                raise SetupError(
                    "recovery_conflict",
                    f"Committed project output changed before recovery: {destination}",
                    exit_code=4,
                )
        store.clear_journal()
        reporter.emit("WARN", "transaction_finalized", "Finalized a committed project apply transaction.")
        return
    for action in reversed(journal.get("actions", [])):
        destination = Path(action["destination"])
        current = snapshot_path(destination)
        if current["kind"] == "absent":
            continue
        if action["kind"] == "file":
            if current["kind"] != "file" or current.get("sha256") != action["sha256"]:
                raise SetupError("recovery_conflict", f"Cannot remove changed project file: {destination}", exit_code=4)
        elif action["kind"] == "symlink":
            if current["kind"] != "symlink" or current.get("link_target") != action["link_target"]:
                raise SetupError("recovery_conflict", f"Cannot remove changed project link: {destination}", exit_code=4)
        destination.unlink()
    store.clear_journal()
    reporter.emit("WARN", "transaction_recovered", "Removed files from an interrupted project apply transaction.")


def recover_pending_transaction(store: StateStore, reporter: Reporter) -> None:
    journal = store.load_journal()
    if journal is None:
        return
    operation = journal.get("operation")
    if operation == "init":
        recover_init_transaction(store, journal, reporter)
    elif operation == "unlink":
        recover_unlink_transaction(store, journal, reporter)
    elif operation == "project-apply":
        recover_project_transaction(store, journal, reporter)
    else:
        raise SetupError("unknown_journal_operation", f"Unknown pending operation: {operation!r}", exit_code=4)


def apply_init(
    repository_root: Path,
    home: Path,
    agents: Sequence[str],
    store: StateStore,
    reporter: Reporter,
    *,
    repair: bool,
) -> None:
    with store.lock():
        recover_pending_transaction(store, reporter)
        state, state_existed = store.load(repository_root)
        specs = build_link_specs(repository_root, home, agents)
        plans = plan_init_links(specs, state, repair=repair)
        emit_link_plan(reporter, plans)
        conflicts = [plan for plan in plans if plan.conflict]
        if conflicts:
            raise SetupError("preflight_conflict", "No changes were applied because preflight found conflicts.")
        tx_id = transaction_id("init")
        reserved: set[str] = set()
        directory_paths: list[Path] = []
        for planned in plans:
            if planned.action in {"create", "replace", "repair"}:
                directory_paths.append(planned.spec.destination.parent)
            if planned.action == "replace":
                planned.backup_path = backup_path_for(planned, store, tx_id, reserved)
                directory_paths.append(planned.backup_path.parent)
        created_directories = [os.fspath(path) for path in missing_directory_paths(directory_paths)]
        journal = {
            "schema_version": 1,
            "id": tx_id,
            "operation": "init",
            "created_at": utc_iso(),
            "state_existed": state_existed,
            "before_state": state,
            "created_directories": created_directories,
            "actions": [journal_action(plan) for plan in plans],
        }
        store.write_journal(journal)
        try:
            ensure_directories(directory_paths)
            new_links = dict(state["links"])
            for planned in plans:
                destination_key = os.fspath(planned.spec.destination)
                if planned.action == "ok":
                    continue
                if planned.action == "owner-update":
                    record = dict(planned.record or {})
                    record["owners"] = merge_owners(record["owners"], planned.spec.owners)
                    record["updated_at"] = utc_iso()
                    new_links[destination_key] = record
                elif planned.action == "adopt":
                    new_links[destination_key] = make_link_record(
                        planned,
                        previous={"kind": "pre-existing-symlink"},
                        owned=False,
                    )
                elif planned.action == "create":
                    if lexists(planned.spec.destination):
                        raise SetupError("destination_changed", f"Destination appeared during setup: {planned.spec.destination}")
                    create_symlink_exclusive(planned.spec.destination, planned.spec.source)
                    new_links[destination_key] = make_link_record(
                        planned,
                        previous={"kind": "absent"},
                        owned=True,
                    )
                elif planned.action == "replace":
                    previous = create_backup(planned)
                    replace_with_symlink(
                        planned.spec.destination,
                        planned.spec.source,
                        expected=planned.snapshot,
                    )
                    new_links[destination_key] = make_link_record(planned, previous=previous, owned=True)
                elif planned.action == "repair":
                    if lexists(planned.spec.destination):
                        raise SetupError("destination_changed", f"Destination appeared during repair: {planned.spec.destination}")
                    create_symlink_exclusive(planned.spec.destination, planned.spec.source)
                    record = dict(planned.record or {})
                    record["owners"] = merge_owners(record["owners"], planned.spec.owners)
                    record["updated_at"] = utc_iso()
                    new_links[destination_key] = record
            next_state = dict(state)
            next_state["repository_root"] = os.fspath(repository_root.resolve(strict=False))
            next_state["links"] = new_links
            store.save_state(next_state)
            store.clear_journal()
        except Exception:
            recover_pending_transaction(store, reporter)
            raise
    reporter.emit("OK", "init_complete", f"Initialized {len(specs)} unique destinations.")


def plan_unlink(
    state: dict[str, Any],
    agents: Sequence[str],
) -> list[dict[str, Any]]:
    selected = set(agents)
    plans: list[dict[str, Any]] = []
    for destination_key, record in sorted(state["links"].items()):
        current_owners = set(record["owners"])
        removed = current_owners & selected
        if not removed:
            continue
        remaining = [agent for agent in SUPPORTED_AGENTS if agent in current_owners - selected]
        destination = Path(destination_key)
        source = Path(record["source"])
        if remaining:
            plans.append(
                {
                    "action": "keep-shared",
                    "destination": destination,
                    "source": source,
                    "record": record,
                    "remaining": remaining,
                    "filesystem_action": False,
                }
            )
            continue
        if not record["owned"]:
            if not link_points_to(destination, source):
                plans.append(
                    {
                        "action": "conflict",
                        "destination": destination,
                        "source": source,
                        "record": record,
                        "remaining": [],
                        "filesystem_action": False,
                    }
                )
            else:
                plans.append(
                    {
                        "action": "forget-adopted",
                        "destination": destination,
                        "source": source,
                        "record": record,
                        "remaining": [],
                        "filesystem_action": False,
                    }
                )
            continue
        if not link_points_to(destination, source):
            plans.append(
                {
                    "action": "conflict",
                    "destination": destination,
                    "source": source,
                    "record": record,
                    "remaining": [],
                    "filesystem_action": False,
                }
            )
            continue
        previous = previous_from_record(record)
        if previous["kind"] == "file":
            backup = Path(previous["backup_path"])
            if backup.is_symlink() or not backup.is_file() or sha256_file(backup) != previous["sha256"]:
                plans.append(
                    {
                        "action": "conflict",
                        "destination": destination,
                        "source": source,
                        "record": record,
                        "remaining": [],
                        "filesystem_action": False,
                    }
                )
                continue
        if previous["kind"] == "symlink":
            backup = Path(previous["backup_path"])
            if not backup.is_symlink() or os.readlink(backup) != previous["link_target"]:
                plans.append(
                    {
                        "action": "conflict",
                        "destination": destination,
                        "source": source,
                        "record": record,
                        "remaining": [],
                        "filesystem_action": False,
                    }
                )
                continue
        plans.append(
            {
                "action": "restore" if previous["kind"] != "absent" else "remove",
                "destination": destination,
                "source": source,
                "record": record,
                "remaining": [],
                "filesystem_action": True,
            }
        )
    return plans


def emit_unlink_plan(reporter: Reporter, plans: Sequence[dict[str, Any]]) -> None:
    for plan in plans:
        action = plan["action"]
        level = "ERROR" if action == "conflict" else ("OK" if action == "keep-shared" else "PLAN")
        messages = {
            "keep-shared": f"Keeping shared destination for: {', '.join(plan['remaining'])}",
            "forget-adopted": "Removing state ownership while leaving the pre-existing symlink untouched.",
            "restore": "Restoring the verified previous setup.",
            "remove": "Removing the managed symlink because no previous setup existed.",
            "conflict": "Destination or backup changed; unlink is refused.",
        }
        reporter.emit(level, action, f"{plan['destination']}: {messages[action]}")


def apply_unlink(
    repository_root: Path,
    store: StateStore,
    agents: Sequence[str],
    reporter: Reporter,
) -> None:
    with store.lock():
        recover_pending_transaction(store, reporter)
        state, state_existed = store.load(repository_root)
        plans = plan_unlink(state, agents)
        emit_unlink_plan(reporter, plans)
        if any(plan["action"] == "conflict" for plan in plans):
            raise SetupError("unlink_conflict", "No changes were applied because unlink preflight found conflicts.")
        tx_id = transaction_id("unlink")
        actions = []
        for plan in plans:
            record = plan["record"]
            actions.append(
                {
                    "action": plan["action"],
                    "destination": os.fspath(plan["destination"]),
                    "source": os.fspath(plan["source"]),
                    "previous": record.get("previous", {"kind": "absent"}),
                    "filesystem_action": plan["filesystem_action"],
                }
            )
        journal = {
            "schema_version": 1,
            "id": tx_id,
            "operation": "unlink",
            "created_at": utc_iso(),
            "state_existed": state_existed,
            "before_state": state,
            "actions": actions,
        }
        store.write_journal(journal)
        try:
            next_links = dict(state["links"])
            for plan in plans:
                key = os.fspath(plan["destination"])
                if plan["action"] == "keep-shared":
                    record = dict(plan["record"])
                    record["owners"] = plan["remaining"]
                    record["updated_at"] = utc_iso()
                    next_links[key] = record
                elif plan["action"] == "forget-adopted":
                    next_links.pop(key, None)
                elif plan["action"] in {"restore", "remove"}:
                    restore_previous(plan["destination"], previous_from_record(plan["record"]))
                    next_links.pop(key, None)
            next_state = dict(state)
            next_state["links"] = next_links
            store.save_state(next_state)
            store.clear_journal()
        except Exception:
            recover_pending_transaction(store, reporter)
            raise
    reporter.emit("OK", "unlink_complete", f"Processed {len(plans)} managed destinations.")
