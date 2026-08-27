from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPTS_DIRECTORY = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIRECTORY))

from agent_setup_lib import cli
from agent_setup_lib.auth_env import auth_env_path, load_auth_environment
from agent_setup_lib.common import Reporter, SetupError


class AuthEnvironmentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="auth-env-test-")
        self.root = Path(self.temporary.name)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def write_env(self, content: str) -> Path:
        path = self.root / ".env"
        path.write_text(content, encoding="utf-8")
        return path

    def test_loads_supported_tokens_and_normalizes_gitlab_host(self) -> None:
        path = self.write_env(
            "GH_TOKEN=github_pat_test\n"
            "GITLAB_TOKEN=glpat-test\n"
            "GITLAB_HOST=gitlab.company.com\n"
        )

        auth = load_auth_environment(path)

        self.assertTrue(auth.github_configured)
        self.assertTrue(auth.gitlab_configured)
        self.assertEqual(auth.gitlab_hostname, "gitlab.company.com")
        self.assertEqual(auth.values["GITLAB_HOST"], "https://gitlab.company.com")
        self.assertNotIn("github_pat_test", repr(auth))
        self.assertNotIn("glpat-test", repr(auth.public_summary()))

    def test_empty_template_is_valid_but_not_configured(self) -> None:
        path = self.write_env("GH_TOKEN=\nGITLAB_TOKEN=\nGITLAB_HOST=https://gitlab.company.com\n")

        auth = load_auth_environment(path)

        self.assertFalse(auth.github_configured)
        self.assertFalse(auth.gitlab_configured)

    def test_rejects_unknown_key(self) -> None:
        path = self.write_env("PATH=/tmp/fake\n")

        with self.assertRaises(SetupError) as raised:
            load_auth_environment(path)

        self.assertEqual(raised.exception.code, "auth_env_key_unsupported")

    def test_rejects_placeholder_token(self) -> None:
        path = self.write_env("GH_TOKEN=REPLACE_WITH_REAL_TOKEN\n")

        with self.assertRaises(SetupError) as raised:
            load_auth_environment(path)

        self.assertEqual(raised.exception.code, "auth_token_invalid")

    def test_gitlab_token_requires_explicit_host(self) -> None:
        path = self.write_env("GITLAB_TOKEN=glpat-test\n")

        with self.assertRaises(SetupError) as raised:
            load_auth_environment(path)

        self.assertEqual(raised.exception.code, "gitlab_host_required")

    def test_does_not_execute_shell_syntax(self) -> None:
        marker = self.root / "executed"
        path = self.write_env(f"GH_TOKEN=$(touch {marker})\n")

        with self.assertRaises(SetupError):
            load_auth_environment(path)

        self.assertFalse(marker.exists())

    def test_relative_auth_path_is_resolved_from_repository(self) -> None:
        self.assertEqual(auth_env_path(self.root, "config/auth.env"), (self.root / "config/auth.env").resolve())


class AuthCommandTests(unittest.TestCase):
    def test_validate_auth_checks_both_providers_without_exposing_tokens(self) -> None:
        with tempfile.TemporaryDirectory(prefix="auth-command-test-") as temporary:
            path = Path(temporary) / ".env"
            path.write_text(
                "GH_TOKEN=github_pat_test\n"
                "GITLAB_TOKEN=glpat-test\n"
                "GITLAB_HOST=https://gitlab.company.com\n",
                encoding="utf-8",
            )
            auth = load_auth_environment(path)
            reporter = Reporter(json_mode=False, command="auth")
            result = {
                "status": "ok",
                "authenticated": True,
                "path": "/usr/bin/tool",
            }

            with mock.patch.object(cli, "command_auth_status", return_value=result) as github_status, mock.patch.object(
                cli,
                "command_gitlab_token_status",
                return_value=result,
            ) as gitlab_status:
                exit_code = cli.validate_auth_environment(auth, reporter)

            self.assertEqual(exit_code, 0)
            github_status.assert_called_once()
            gitlab_status.assert_called_once()
            for call in (github_status.call_args, gitlab_status.call_args):
                environment = call.kwargs["environment"]
                self.assertEqual(environment["GH_TOKEN"], "github_pat_test")
                self.assertEqual(environment["GITLAB_TOKEN"], "glpat-test")
            self.assertNotIn("GH_TOKEN", os.environ)
            self.assertNotIn("GITLAB_TOKEN", os.environ)

    def test_partial_auth_can_be_validated_for_tools(self) -> None:
        with tempfile.TemporaryDirectory(prefix="auth-command-test-") as temporary:
            path = Path(temporary) / ".env"
            path.write_text("GH_TOKEN=github_pat_test\n", encoding="utf-8")
            auth = load_auth_environment(path)
            reporter = Reporter(json_mode=False, command="tools")
            result = {"status": "ok", "authenticated": True, "path": "/usr/bin/gh"}

            with mock.patch.object(cli, "command_auth_status", return_value=result) as status:
                exit_code = cli.validate_auth_environment(auth, reporter, require_all=False)

            self.assertEqual(exit_code, 0)
            status.assert_called_once()
            self.assertEqual(status.call_args.args[0], "gh")


if __name__ == "__main__":
    unittest.main()
