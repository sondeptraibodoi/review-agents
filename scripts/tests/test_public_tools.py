from __future__ import annotations

import io
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock


SCRIPTS_DIRECTORY = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIRECTORY))

from agent_setup_lib import public_tools
from agent_setup_lib import doctor as doctor_module
from agent_setup_lib import cli as cli_module
from agent_setup_lib.common import Reporter, SetupError


def available_prerequisites() -> dict[str, dict[str, object]]:
    results: dict[str, dict[str, object]] = {}
    for name in (*public_tools.LOCAL_REQUIRED_TOOLS, *public_tools.LOCAL_RECOMMENDED_TOOLS):
        version = "v22.19.0" if name == "node" else f"{name} test"
        results[name] = {
            "status": "ok",
            "command": name,
            "path": f"/usr/bin/{name}",
            "version": version,
        }
    return results


class BootstrapParsingTests(unittest.TestCase):
    def test_platform_status_recognizes_macos(self) -> None:
        with mock.patch.object(doctor_module.platform, "system", return_value="Darwin"), mock.patch.object(
            doctor_module.platform,
            "release",
            return_value="25.0.0",
        ):
            result = doctor_module.platform_status()

        self.assertTrue(result["supported"])
        self.assertTrue(result["is_macos"])
        self.assertFalse(result["is_linux"])
        self.assertFalse(result["is_wsl"])

    def test_tools_install_is_a_distinct_mutating_mode(self) -> None:
        parser = cli_module.build_parser()
        args = parser.parse_args(["tools", "--install"])

        self.assertTrue(args.install)
        self.assertFalse(args.apply)
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            parser.parse_args(["tools", "--install", "--apply"])

    def test_agy_is_presence_checked_without_launching_interactive_cli(self) -> None:
        with mock.patch.object(doctor_module.shutil, "which", return_value="/home/test/.local/bin/agy"), mock.patch.object(
            doctor_module.subprocess,
            "run",
        ) as run:
            result = doctor_module.command_version("agy")

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["version"], "presence-only")
        run.assert_not_called()

    def test_tmux_uses_its_supported_version_flag(self) -> None:
        completed = subprocess.CompletedProcess(
            args=["/usr/bin/tmux", "-V"],
            returncode=0,
            stdout="tmux 3.2a\n",
            stderr="",
        )
        with mock.patch.object(doctor_module.shutil, "which", return_value="/usr/bin/tmux"), mock.patch.object(
            doctor_module.subprocess,
            "run",
            return_value=completed,
        ) as run:
            result = doctor_module.command_version("tmux")

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["version"], "tmux 3.2a")
        self.assertEqual(run.call_args.args[0], ["/usr/bin/tmux", "-V"])

    def test_codex_version_allows_a_slow_cold_start(self) -> None:
        completed = subprocess.CompletedProcess(
            args=["/home/test/.local/bin/codex", "--version"],
            returncode=0,
            stdout="codex-cli 0.150.1\n",
            stderr="",
        )
        with mock.patch.object(
            doctor_module.shutil,
            "which",
            return_value="/home/test/.local/bin/codex",
        ), mock.patch.object(
            doctor_module.subprocess,
            "run",
            return_value=completed,
        ) as run:
            result = doctor_module.command_version("codex")

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["version"], "codex-cli 0.150.1")
        self.assertEqual(run.call_args.kwargs["timeout"], 15)

    def test_auth_diagnostic_redacts_token(self) -> None:
        completed = subprocess.CompletedProcess(
            args=["/usr/bin/glab", "auth", "status"],
            returncode=1,
            stdout="",
            stderr="ERROR: rejected glpat-secret\n",
        )
        with mock.patch.object(doctor_module.shutil, "which", return_value="/usr/bin/glab"), mock.patch.object(
            doctor_module.subprocess,
            "run",
            return_value=completed,
        ):
            result = doctor_module.command_auth_status(
                "glab",
                environment={"GITLAB_TOKEN": "glpat-secret"},
                hostname="git.example.com",
            )

        self.assertNotIn("glpat-secret", result["diagnostic"])
        self.assertIn("<redacted>", result["diagnostic"])

    def test_github_missing_required_scope_is_not_authenticated(self) -> None:
        completed = subprocess.CompletedProcess(
            args=["/usr/bin/gh", "auth", "status"],
            returncode=0,
            stdout="Missing required token scopes: 'read:org'\n",
            stderr="",
        )
        with mock.patch.object(doctor_module.shutil, "which", return_value="/usr/bin/gh"), mock.patch.object(
            doctor_module.subprocess,
            "run",
            return_value=completed,
        ):
            result = doctor_module.command_auth_status("gh", environment={"GH_TOKEN": "ghp-secret"})

        self.assertFalse(result["authenticated"])
        self.assertEqual(result["status"], "insufficient-scopes")

    def test_gitlab_env_token_is_validated_with_api_user(self) -> None:
        completed = subprocess.CompletedProcess(
            args=["/usr/bin/glab", "api", "user"],
            returncode=0,
            stdout="",
            stderr="",
        )
        environment = {"GITLAB_TOKEN": "glpat-secret", "GITLAB_HOST": "https://git.example.com"}
        with mock.patch.object(doctor_module.shutil, "which", return_value="/usr/bin/glab"), mock.patch.object(
            doctor_module.subprocess,
            "run",
            return_value=completed,
        ) as run:
            result = doctor_module.command_gitlab_token_status(
                environment=environment,
                hostname="git.example.com",
            )

        self.assertTrue(result["authenticated"])
        self.assertEqual(
            run.call_args.args[0],
            ["/usr/bin/glab", "api", "user", "--hostname", "git.example.com", "--silent"],
        )

    def test_parses_firstmate_machine_lines(self) -> None:
        report = public_tools.parse_firstmate_bootstrap_output(
            "\n".join(
                (
                    "MISSING: lavish-axi (install: npm install -g lavish-axi)",
                    "MISSING: treehouse (install: curl ...)",
                    "MISSING_MANUAL: herdr (install manually)",
                    "NEEDS_GH_AUTH",
                    "MISSING: lavish-axi (duplicate)",
                )
            )
        )

        self.assertEqual(report.missing, ("lavish-axi", "treehouse"))
        self.assertEqual(report.manual, ("herdr",))
        self.assertTrue(report.needs_gh_auth)
        self.assertEqual(report.actionable, ())

    def test_backend_diagnostic_blocks_bootstrap_install(self) -> None:
        report = public_tools.parse_firstmate_bootstrap_output(
            "BACKEND_INVALID: unknown (known: tmux herdr zellij orca cmux)\n"
        )

        self.assertEqual(
            public_tools.blocking_bootstrap_diagnostics(report),
            ["BACKEND_INVALID: unknown (known: tmux herdr zellij orca cmux)"],
        )

    def test_tmux_delegation_set_matches_firstmate_contract(self) -> None:
        self.assertEqual(
            set(public_tools.FIRSTMATE_DELEGATED_TOOLS),
            {
                "no-mistakes",
                "gh-axi",
                "chrome-devtools-axi",
                "lavish-axi",
                "tasks-axi",
                "quota-axi",
                "treehouse",
            },
        )

    def test_node_22_19_is_required(self) -> None:
        results = available_prerequisites()
        results["node"]["version"] = "v22.18.0"

        self.assertEqual(public_tools.prerequisite_blockers(results), ["node>=22.19"])

    def test_windows_npm_path_is_not_accepted_as_wsl_native(self) -> None:
        results = available_prerequisites()
        results["npm"]["path"] = "/mnt/c/nvm4w/nodejs/npm"

        self.assertEqual(public_tools.prerequisite_blockers(results), ["npm (native executable required)"])


class PublicToolsLifecycleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="public-tools-test-")
        self.home = Path(self.temporary.name) / "home"
        self.home.mkdir()
        self.reporter = Reporter(json_mode=False, command="tools")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_checkout_without_tracked_upstream_is_not_executed(self) -> None:
        checkout = self.home / "agent-tools/firstmate"
        inspection = {
            "status": "present",
            "remote_correct": True,
            "bootstrap_present": True,
            "dirty": False,
            "upstream": None,
            "ahead": None,
            "divergent": False,
        }
        with mock.patch.object(
            public_tools,
            "inspect_firstmate_checkout",
            return_value=inspection,
        ), self.assertRaises(SetupError) as raised:
            public_tools.validate_firstmate_checkout(checkout, executable=True)

        self.assertEqual(raised.exception.code, "firstmate_upstream_missing")

    def test_dry_run_without_checkout_does_not_create_files(self) -> None:
        with mock.patch.object(
            public_tools,
            "inspect_local_prerequisites",
            return_value=available_prerequisites(),
        ), redirect_stdout(io.StringIO()):
            result = public_tools.run_public_tools(
                home=self.home,
                configured_firstmate_dir=None,
                apply=False,
                skip_gnhf=False,
                reporter=self.reporter,
            )

        self.assertEqual(result, 0)
        self.assertFalse((self.home / "agent-tools").exists())
        codes = [event["code"] for event in self.reporter.events]
        self.assertIn("firstmate_clone", codes)
        self.assertIn("dry_run", codes)

    def test_install_mode_repairs_prerequisites_before_firstmate(self) -> None:
        checkout = self.home / "agent-tools/firstmate"
        (checkout / ".git").mkdir(parents=True)
        before = available_prerequisites()
        before["node"]["version"] = "v18.20.8"
        before["gh"] = {"status": "missing", "command": "gh"}
        before["glab"] = {"status": "missing", "command": "glab"}
        after = available_prerequisites()
        complete = public_tools.BootstrapReport(
            missing=(),
            manual=(),
            needs_gh_auth=False,
            output="",
        )
        inspection = {
            "status": "present",
            "remote_correct": True,
            "bootstrap_present": True,
            "dirty": False,
            "upstream": "origin/main",
            "ahead": 0,
            "behind": 0,
            "divergent": False,
        }

        with mock.patch.object(
            public_tools,
            "inspect_local_prerequisites",
            side_effect=(before, after),
        ), mock.patch.object(
            public_tools,
            "install_system_prerequisites",
        ) as install_system, mock.patch.object(
            public_tools,
            "validate_firstmate_checkout",
            return_value=inspection,
        ), mock.patch.object(
            public_tools,
            "run_firstmate_detect",
            side_effect=(complete, complete),
        ), mock.patch.object(
            public_tools,
            "install_gnhf",
        ), mock.patch.object(
            public_tools,
            "browser_status",
            return_value={"available": True, "commands": ["chromium"], "browser_url_configured": False},
        ), redirect_stdout(io.StringIO()):
            result = public_tools.run_public_tools(
                home=self.home,
                configured_firstmate_dir=None,
                apply=True,
                skip_gnhf=False,
                reporter=self.reporter,
                install_prerequisites=True,
            )

        self.assertEqual(result, 0)
        install_system.assert_called_once_with(self.home, before, self.reporter)

    def test_apply_delegates_only_firstmate_owned_tools(self) -> None:
        checkout = self.home / "agent-tools/firstmate"
        (checkout / ".git").mkdir(parents=True)
        before = public_tools.BootstrapReport(
            missing=("git", "lavish-axi", "treehouse", "gnhf"),
            manual=(),
            needs_gh_auth=False,
            output="",
        )
        installable = public_tools.BootstrapReport(
            missing=("lavish-axi", "treehouse"),
            manual=(),
            needs_gh_auth=False,
            output="",
        )
        complete = public_tools.BootstrapReport(
            missing=(),
            manual=(),
            needs_gh_auth=False,
            output="",
        )
        inspection = {
            "status": "present",
            "remote_correct": True,
            "bootstrap_present": True,
            "dirty": False,
            "ahead": 0,
            "behind": 0,
            "divergent": False,
        }

        self.assertEqual(
            public_tools.classify_firstmate_missing(before),
            {
                "delegated": ["lavish-axi", "treehouse"],
                "system": ["git"],
                "unknown": ["gnhf"],
                "manual": [],
            },
        )

        with mock.patch.object(
            public_tools,
            "inspect_local_prerequisites",
            return_value=available_prerequisites(),
        ), mock.patch.object(
            public_tools,
            "validate_firstmate_checkout",
            return_value=inspection,
        ), mock.patch.object(
            public_tools,
            "run_firstmate_detect",
            side_effect=(installable, complete),
        ), mock.patch.object(
            public_tools,
            "install_firstmate_delegated",
        ) as delegated, mock.patch.object(
            public_tools,
            "install_gnhf",
        ) as gnhf, mock.patch.object(
            public_tools,
            "browser_status",
            return_value={"available": True, "commands": ["chromium"], "browser_url_configured": False},
        ), redirect_stdout(io.StringIO()):
            result = public_tools.run_public_tools(
                home=self.home,
                configured_firstmate_dir=None,
                apply=True,
                skip_gnhf=False,
                reporter=self.reporter,
            )

        self.assertEqual(result, 0)
        delegated.assert_called_once_with(checkout, ["lavish-axi", "treehouse"])
        gnhf.assert_called_once_with(self.reporter)

    def test_system_tool_reported_by_firstmate_blocks_install(self) -> None:
        checkout = self.home / "agent-tools/firstmate"
        (checkout / ".git").mkdir(parents=True)
        report = public_tools.BootstrapReport(
            missing=("gh",),
            manual=(),
            needs_gh_auth=False,
            output="",
        )
        inspection = {
            "status": "present",
            "remote_correct": True,
            "bootstrap_present": True,
            "dirty": False,
            "ahead": 0,
            "behind": 0,
            "divergent": False,
        }

        with mock.patch.object(
            public_tools,
            "inspect_local_prerequisites",
            return_value=available_prerequisites(),
        ), mock.patch.object(
            public_tools,
            "validate_firstmate_checkout",
            return_value=inspection,
        ), mock.patch.object(
            public_tools,
            "run_firstmate_detect",
            return_value=report,
        ), redirect_stdout(io.StringIO()), self.assertRaises(SetupError) as raised:
            public_tools.run_public_tools(
                home=self.home,
                configured_firstmate_dir=None,
                apply=True,
                skip_gnhf=True,
                reporter=self.reporter,
            )

        self.assertEqual(raised.exception.code, "firstmate_preflight_blocked")


if __name__ == "__main__":
    unittest.main()
