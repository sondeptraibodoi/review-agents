from __future__ import annotations

import argparse
import contextlib
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "agent_setup.py"
SPEC = importlib.util.spec_from_file_location("agent_setup", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Cannot import {SCRIPT_PATH}")
agent_setup = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = agent_setup
SPEC.loader.exec_module(agent_setup)
from agent_setup_lib import doctor as doctor_module
from agent_setup_lib import project as project_module

REPOSITORY_ROOT = SCRIPT_PATH.parent.parent


def valid_proposal() -> str:
    sections = []
    for heading in agent_setup.REQUIRED_PROPOSAL_HEADINGS:
        sections.extend((heading, "", "Verified test content.", ""))
    return "\n".join(sections).rstrip() + "\n"


class TemporaryHomeTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="agent-setup-test-")
        self.root = Path(self.temporary.name)
        self.home = self.root / "home"
        self.home.mkdir()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def run_main(self, arguments: list[str]) -> tuple[int, str]:
        output = io.StringIO()
        common = [
            "--home",
            os.fspath(self.home),
            "--repo-root",
            os.fspath(REPOSITORY_ROOT),
            "--allow-root",
        ]
        with contextlib.redirect_stdout(output):
            return agent_setup.main([*arguments, *common]), output.getvalue()


class ParsingTests(unittest.TestCase):
    def test_parse_agents_deduplicates_and_normalizes_antigravity(self) -> None:
        self.assertEqual(
            agent_setup.parse_agents("codex, antigravity, codex, claude"),
            ("codex", "agy", "claude"),
        )

    def test_parse_agents_rejects_unknown_value(self) -> None:
        with self.assertRaisesRegex(agent_setup.SetupError, "Unsupported agent"):
            agent_setup.parse_agents("codex,unknown")

    def test_compatibility_init_alias(self) -> None:
        self.assertEqual(
            agent_setup.normalize_compatibility_argv(["--init=codex,agy", "--apply"]),
            ["init", "--agents", "codex,agy", "--apply"],
        )

    def test_compatibility_project_alias(self) -> None:
        self.assertEqual(
            agent_setup.normalize_compatibility_argv(
                ["--project_setup=https://gitlab.example/a/b.git", "--agents=codex"]
            ),
            [
                "project-setup",
                "--url",
                "https://gitlab.example/a/b.git",
                "--agents=codex",
            ],
        )

    def test_combined_model_and_effort(self) -> None:
        self.assertEqual(
            agent_setup.normalize_model_and_effort("gpt-5.6-sol_xhigh", None),
            ("gpt-5.6-sol", "xhigh"),
        )

    def test_conflicting_model_effort_is_rejected(self) -> None:
        with self.assertRaisesRegex(agent_setup.SetupError, "suffix requests xhigh"):
            agent_setup.normalize_model_and_effort("gpt-5.6-sol_xhigh", "low")

    def test_repository_url_formats(self) -> None:
        https = agent_setup.parse_repository_url("https://gitlab.example/group/repo.git")
        ssh = agent_setup.parse_repository_url("git@gitlab.example:group/repo.git")
        self.assertEqual(https.canonical, "gitlab.example/group/repo")
        self.assertEqual(ssh.canonical, https.canonical)

    def test_repository_url_rejects_credentials_and_bad_port(self) -> None:
        with self.assertRaises(agent_setup.SetupError):
            agent_setup.parse_repository_url("https://user:token@gitlab.example/group/repo")
        with self.assertRaisesRegex(agent_setup.SetupError, "invalid port"):
            agent_setup.parse_repository_url("ssh://git@gitlab.example:notaport/group/repo")


class SourceAndMappingTests(TemporaryHomeTestCase):
    def test_sources_have_valid_skill_frontmatter(self) -> None:
        metadata = agent_setup.validate_sources(REPOSITORY_ROOT)
        self.assertEqual(
            set(metadata),
            {
                "tuln-opinions",
                "python-tools",
                "lavish",
                "chrome-devtools-axi",
            },
        )

    def test_axi_skill_routes_use_installed_commands_and_define_conditions(self) -> None:
        lavish = (REPOSITORY_ROOT / "skills/LAVISH.md").read_text(encoding="utf-8")
        chrome = (REPOSITORY_ROOT / "skills/CHROME_DEVTOOLS_AXI.md").read_text(encoding="utf-8")

        self.assertIn("command -v lavish-axi", lavish)
        self.assertIn("lavish-axi --help", lavish)
        self.assertIn("Do not load this skill", lavish)
        self.assertIn("do not download another copy with `npx -y`", lavish)

        self.assertIn("command -v chrome-devtools-axi", chrome)
        self.assertIn("chrome-devtools-axi --help", chrome)
        self.assertIn("browser console", chrome)
        self.assertIn("network", chrome)
        self.assertIn("screenshot", chrome)
        self.assertIn("do not download another copy with `npx -y`", chrome)

    def test_shared_destinations_are_deduplicated_with_owners(self) -> None:
        specs = agent_setup.build_link_specs(
            REPOSITORY_ROOT,
            self.home,
            ("codex", "gemini", "agy", "claude"),
        )
        self.assertEqual(len(specs), 19)
        codex_skill = next(
            spec for spec in specs if spec.destination == self.home / ".agents/skills/python-tools/SKILL.md"
        )
        self.assertEqual(codex_skill.owners, ("codex",))
        agy_skill = next(
            spec
            for spec in specs
            if spec.destination == self.home / ".gemini/antigravity-cli/skills/python-tools/SKILL.md"
        )
        self.assertEqual(agy_skill.owners, ("agy",))
        codex_lavish = next(
            spec
            for spec in specs
            if spec.destination == self.home / ".agents/skills/lavish/SKILL.md"
        )
        self.assertEqual(codex_lavish.source, REPOSITORY_ROOT / "skills/LAVISH.md")
        agy_chrome = next(
            spec
            for spec in specs
            if spec.destination
            == self.home / ".gemini/antigravity-cli/skills/chrome-devtools-axi/SKILL.md"
        )
        self.assertEqual(
            agy_chrome.source,
            REPOSITORY_ROOT / "skills/CHROME_DEVTOOLS_AXI.md",
        )
        gemini_file = next(spec for spec in specs if spec.destination == self.home / ".gemini/GEMINI.md")
        self.assertEqual(gemini_file.owners, ("gemini", "agy"))

    def test_agy_project_mapping_includes_gemini_file(self) -> None:
        actions = agent_setup.project_destinations(self.root / "project", ("agy",))
        destinations = {Path(action["destination"]).name for action in actions}
        self.assertEqual(destinations, {"AGENTS.md", "GEMINI.md"})


class InitLifecycleTests(TemporaryHomeTestCase):
    def test_dry_run_does_not_create_home_entries_or_state(self) -> None:
        code, output = self.run_main(["init", "--agents", "codex"])
        self.assertEqual(code, 0, output)
        self.assertFalse((self.home / ".codex").exists())
        self.assertFalse((self.home / ".agents").exists())
        self.assertFalse((self.home / ".local").exists())

    def test_init_is_idempotent_and_unlink_restores_previous_file(self) -> None:
        old_path = self.home / ".codex/AGENTS.md"
        old_path.parent.mkdir(parents=True)
        old_path.write_text("old instructions\n", encoding="utf-8")

        code, output = self.run_main(
            ["init", "--agents", "codex,gemini,agy,claude", "--apply"]
        )
        self.assertEqual(code, 0, output)
        self.assertTrue(old_path.is_symlink())
        self.assertEqual((self.home / ".codex/AGENTS-bak.md").read_text(), "old instructions\n")
        self.assertTrue((self.home / ".gemini/GEMINI.md").is_symlink())
        self.assertTrue((self.home / ".claude/CLAUDE.md").is_symlink())

        state_path = self.home / ".local/state/agent-advance-setup/state.json"
        state_before = json.loads(state_path.read_text(encoding="utf-8"))
        self.assertEqual(len(state_before["links"]), 19)
        self.assertEqual(
            state_before["links"][os.fspath(self.home / ".gemini/GEMINI.md")]["owners"],
            ["gemini", "agy"],
        )

        code, output = self.run_main(
            ["init", "--agents", "codex,gemini,agy,claude", "--apply"]
        )
        self.assertEqual(code, 0, output)
        self.assertEqual(list((self.home / ".codex").glob("AGENTS-bak*.md")), [self.home / ".codex/AGENTS-bak.md"])

        code, output = self.run_main(["unlink", "--agents", "codex", "--apply"])
        self.assertEqual(code, 0, output)
        self.assertFalse(old_path.is_symlink())
        self.assertEqual(old_path.read_text(encoding="utf-8"), "old instructions\n")
        self.assertFalse(os.path.lexists(self.home / ".agents/skills/python-tools/SKILL.md"))
        self.assertFalse(os.path.lexists(self.home / ".agents/skills/lavish/SKILL.md"))
        self.assertFalse(os.path.lexists(self.home / ".agents/skills/chrome-devtools-axi/SKILL.md"))
        self.assertTrue((self.home / ".gemini/skills/python-tools/SKILL.md").is_symlink())

        code, output = self.run_main(["unlink", "--agents", "gemini,agy,claude", "--apply"])
        self.assertEqual(code, 0, output)
        self.assertFalse(os.path.lexists(self.home / ".gemini/GEMINI.md"))
        self.assertFalse(os.path.lexists(self.home / ".gemini/skills/python-tools/SKILL.md"))
        self.assertFalse(os.path.lexists(self.home / ".gemini/antigravity-cli/skills/python-tools/SKILL.md"))
        self.assertFalse(os.path.lexists(self.home / ".claude/CLAUDE.md"))

    def test_existing_correct_symlink_is_adopted_and_left_on_unlink(self) -> None:
        destination = self.home / ".codex/AGENTS.md"
        destination.parent.mkdir(parents=True)
        destination.symlink_to(REPOSITORY_ROOT / "global/AGENTS.md")
        code, output = self.run_main(["init", "--agents", "codex", "--apply"])
        self.assertEqual(code, 0, output)

        code, output = self.run_main(["unlink", "--agents", "codex", "--apply"])
        self.assertEqual(code, 0, output)
        self.assertTrue(destination.is_symlink())

    def test_existing_backup_is_never_overwritten(self) -> None:
        destination = self.home / ".codex/AGENTS.md"
        destination.parent.mkdir(parents=True)
        destination.write_text("current\n", encoding="utf-8")
        reserved = self.home / ".codex/AGENTS-bak.md"
        reserved.write_text("keep\n", encoding="utf-8")

        code, output = self.run_main(["init", "--agents", "codex", "--apply"])
        self.assertEqual(code, 0, output)
        self.assertEqual(reserved.read_text(encoding="utf-8"), "keep\n")
        backups = list((self.home / ".codex").glob("AGENTS-bak-*.md"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_text(encoding="utf-8"), "current\n")

    def test_external_change_to_managed_link_is_a_conflict(self) -> None:
        code, output = self.run_main(["init", "--agents", "codex", "--apply"])
        self.assertEqual(code, 0, output)
        destination = self.home / ".codex/AGENTS.md"
        destination.unlink()
        destination.write_text("user change\n", encoding="utf-8")

        code, output = self.run_main(["init", "--agents", "codex", "--apply"])
        self.assertEqual(code, 2, output)
        self.assertIn("previously managed destination was changed", output)
        self.assertEqual(destination.read_text(encoding="utf-8"), "user change\n")

    def test_missing_owned_link_requires_explicit_repair(self) -> None:
        code, output = self.run_main(["init", "--agents", "codex", "--apply"])
        self.assertEqual(code, 0, output)
        destination = self.home / ".codex/AGENTS.md"
        destination.unlink()

        code, _ = self.run_main(["init", "--agents", "codex", "--apply"])
        self.assertEqual(code, 2)
        code, output = self.run_main(["init", "--agents", "codex", "--repair", "--apply"])
        self.assertEqual(code, 0, output)
        self.assertTrue(destination.is_symlink())

    def test_broken_symlink_is_backed_up_and_restored(self) -> None:
        destination = self.home / ".codex/AGENTS.md"
        destination.parent.mkdir(parents=True)
        destination.symlink_to("missing-old-target.md")
        code, output = self.run_main(["init", "--agents", "codex", "--apply"])
        self.assertEqual(code, 0, output)
        code, output = self.run_main(["unlink", "--agents", "codex", "--apply"])
        self.assertEqual(code, 0, output)
        self.assertTrue(destination.is_symlink())
        self.assertEqual(os.readlink(destination), "missing-old-target.md")

    def test_init_migrates_managed_legacy_codex_skill_links(self) -> None:
        code, output = self.run_main(["init", "--agents", "codex", "--apply"])
        self.assertEqual(code, 0, output)

        current = self.home / ".agents/skills/lavish/SKILL.md"
        legacy = self.home / ".codex/skills/lavish/SKILL.md"
        legacy.parent.mkdir(parents=True)
        legacy.symlink_to(REPOSITORY_ROOT / "skills/LAVISH.md")

        state_path = self.home / ".local/state/agent-advance-setup/state.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        record = dict(state["links"][os.fspath(current)])
        record["destination"] = os.fspath(legacy)
        record["previous"] = {"kind": "absent"}
        state["links"][os.fspath(legacy)] = record
        state_path.write_text(json.dumps(state), encoding="utf-8")

        code, output = self.run_main(["init", "--agents", "codex", "--apply"])

        self.assertEqual(code, 0, output)
        self.assertTrue(current.is_symlink())
        self.assertFalse(os.path.lexists(legacy))
        migrated_state = json.loads(state_path.read_text(encoding="utf-8"))
        self.assertNotIn(os.fspath(legacy), migrated_state["links"])
        self.assertIn("legacy_skill_migration_complete", output)

    def test_doctor_fails_when_a_routed_public_cli_is_missing(self) -> None:
        code, output = self.run_main(["init", "--agents", "codex", "--apply"])
        self.assertEqual(code, 0, output)
        empty_env = self.root / "empty.env"
        empty_env.write_text("", encoding="utf-8")

        def command_result(command: str) -> dict[str, str]:
            if command == "lavish-axi":
                return {"status": "missing", "command": command}
            return {
                "status": "ok",
                "command": command,
                "path": f"/usr/bin/{command}",
                "version": "test",
            }

        authenticated = {"authenticated": True, "status": "ok"}
        with mock.patch.object(
            doctor_module,
            "command_version",
            side_effect=command_result,
        ), mock.patch.object(
            doctor_module,
            "command_auth_status",
            return_value=authenticated,
        ):
            code, output = self.run_main(
                [
                    "doctor",
                    "--agents",
                    "codex",
                    "--env-file",
                    os.fspath(empty_env),
                ]
            )

        self.assertEqual(code, 2, output)
        self.assertIn("routed_tool: lavish: lavish-axi is missing.", output)


class ProposalTests(TemporaryHomeTestCase):
    def test_validate_proposal_requires_exact_heading_lines(self) -> None:
        path = self.root / "proposal.md"
        path.write_text(valid_proposal(), encoding="utf-8")
        self.assertEqual(agent_setup.validate_proposal(path), valid_proposal())
        path.write_text(valid_proposal().replace("# Project Agent Instructions", "Prefix # Project Agent Instructions", 1))
        with self.assertRaises(agent_setup.SetupError):
            agent_setup.validate_proposal(path)

    def test_project_apply_creates_agent_files_from_bound_proposal(self) -> None:
        repository = self.root / "project"
        (repository / ".git").mkdir(parents=True)
        store = agent_setup.StateStore(self.home)
        proposal_id = "project-test"
        directory = agent_setup.proposal_directory(store, proposal_id)
        directory.mkdir(parents=True)
        text = valid_proposal()
        proposal_path = directory / "AGENTS.proposed.md"
        proposal_path.write_text(text, encoding="utf-8")
        metadata_path = directory / "metadata.json"
        metadata = {
            "schema_version": 1,
            "proposal_id": proposal_id,
            "repository_url": "https://gitlab.example/group/project.git",
            "repository_canonical": "gitlab.example/group/project",
            "repository_path": os.fspath(repository),
            "commit": "abc123",
            "generator": "codex",
            "model": "gpt-5.6-sol",
            "effort": "xhigh",
            "agents": ["codex", "claude", "agy"],
            "prompt_sha256": agent_setup.sha256_text(agent_setup.project_prompt()),
            "schema_sha256": agent_setup.sha256_text("\n".join(agent_setup.REQUIRED_PROPOSAL_HEADINGS)),
            "proposal_sha256": agent_setup.sha256_text(text),
            "generated_at": agent_setup.utc_iso(),
            "applied_at": None,
        }
        store._atomic_write_json(metadata_path, metadata)
        args = argparse.Namespace(proposal_id=proposal_id)
        reporter = agent_setup.Reporter(json_mode=False, command="project-setup")
        with mock.patch.object(project_module, "repository_status", return_value={"head": "abc123"}), mock.patch.object(
            project_module,
            "git_value",
            return_value="https://gitlab.example/group/project.git",
        ):
            agent_setup.apply_project(args, REPOSITORY_ROOT, store, reporter)

        self.assertEqual((repository / "AGENTS.md").read_text(encoding="utf-8"), text)
        self.assertEqual(os.readlink(repository / "CLAUDE.md"), "AGENTS.md")
        self.assertEqual(os.readlink(repository / "GEMINI.md"), "AGENTS.md")

    @unittest.skipUnless(os.name == "posix", "Generator isolation is validated on WSL2/Linux.")
    def test_project_analysis_uses_codex_contract_and_normalizes_model_suffix(self) -> None:
        repository = self.root / "clones/project"
        repository.mkdir(parents=True)
        subprocess.run(["git", "init", "-q", os.fspath(repository)], check=True)
        subprocess.run(["git", "-C", os.fspath(repository), "config", "user.email", "test@example.com"], check=True)
        subprocess.run(["git", "-C", os.fspath(repository), "config", "user.name", "Test"], check=True)
        (repository / "README.md").write_text("# Test project\n", encoding="utf-8")
        subprocess.run(["git", "-C", os.fspath(repository), "add", "README.md"], check=True)
        subprocess.run(["git", "-C", os.fspath(repository), "commit", "-qm", "initial"], check=True)
        remote = "https://gitlab.example/group/project.git"
        subprocess.run(["git", "-C", os.fspath(repository), "remote", "add", "origin", remote], check=True)

        fixture = self.root / "valid-proposal.md"
        fixture.write_text(valid_proposal(), encoding="utf-8")
        fake_bin = self.root / "bin"
        fake_bin.mkdir()
        fake_codex = fake_bin / "codex"
        fake_codex.write_text(
            """#!/bin/sh
set -eu
if [ "$1" = "exec" ] && [ "${2:-}" = "--help" ]; then
    printf '%s\n' '--sandbox --ephemeral --output-last-message --skip-git-repo-check --model --cd --config'
    exit 0
fi
output=''
while [ "$#" -gt 0 ]; do
    if [ "$1" = "--output-last-message" ]; then
        shift
        output=$1
    fi
    shift
done
cp "$FAKE_PROPOSAL" "$output"
""",
            encoding="utf-8",
        )
        fake_codex.chmod(0o755)
        environment = {
            "PATH": f"{fake_bin}{os.pathsep}{os.environ['PATH']}",
            "FAKE_PROPOSAL": os.fspath(fixture),
        }
        with mock.patch.dict(os.environ, environment):
            code, output = self.run_main(
                [
                    "project-setup",
                    "--url",
                    remote,
                    "--dest",
                    os.fspath(repository),
                    "--clone-root",
                    os.fspath(self.root / "clones"),
                    "--agents",
                    "codex,agy",
                    "--model",
                    "gpt-5.6-sol_xhigh",
                    "--json",
                ]
            )
        self.assertEqual(code, 0, output)
        report = json.loads(output)
        proposal_id = report["data"]["proposal_id"]
        directory = self.home / ".local/state/agent-advance-setup/projects" / proposal_id
        metadata = json.loads((directory / "metadata.json").read_text(encoding="utf-8"))
        self.assertEqual(metadata["model"], "gpt-5.6-sol")
        self.assertEqual(metadata["effort"], "xhigh")
        self.assertEqual(metadata["agents"], ["codex", "agy"])
        self.assertEqual((directory / "AGENTS.proposed.md").read_text(encoding="utf-8"), valid_proposal())
        self.assertEqual((directory.stat().st_mode & 0o777), 0o700)
        self.assertEqual(((directory / "AGENTS.proposed.md").stat().st_mode & 0o777), 0o600)


class SnapshotTests(TemporaryHomeTestCase):
    @unittest.skipUnless(os.name == "posix", "Git archive behavior is validated on WSL2/Linux.")
    def test_tracked_snapshot_excludes_untracked_files(self) -> None:
        repository = self.root / "repo"
        repository.mkdir()
        subprocess.run(["git", "init", "-q", os.fspath(repository)], check=True)
        subprocess.run(["git", "-C", os.fspath(repository), "config", "user.email", "test@example.com"], check=True)
        subprocess.run(["git", "-C", os.fspath(repository), "config", "user.name", "Test"], check=True)
        (repository / "tracked.txt").write_text("tracked\n", encoding="utf-8")
        subprocess.run(["git", "-C", os.fspath(repository), "add", "tracked.txt"], check=True)
        subprocess.run(["git", "-C", os.fspath(repository), "commit", "-qm", "initial"], check=True)
        (repository / "secret.env").write_text("TOKEN=do-not-copy\n", encoding="utf-8")
        snapshot = self.root / "snapshot"
        agent_setup.create_tracked_snapshot(repository, snapshot)
        self.assertEqual((snapshot / "tracked.txt").read_text(), "tracked\n")
        self.assertFalse((snapshot / "secret.env").exists())


if __name__ == "__main__":
    unittest.main()
