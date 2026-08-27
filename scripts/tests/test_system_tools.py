from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPTS_DIRECTORY = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIRECTORY))

from agent_setup_lib import system_tools
from agent_setup_lib.common import Reporter, SetupError


def prerequisite_results() -> dict[str, dict[str, object]]:
    return {
        "git": {"status": "ok", "path": "/usr/bin/git", "version": "git 2.34"},
        "node": {"status": "ok", "path": "/home/test/.nvm/node", "version": "v22.19.0"},
        "npm": {"status": "ok", "path": "/home/test/.nvm/npm", "version": "10.8.0"},
        "tmux": {"status": "ok", "path": "/usr/bin/tmux", "version": "tmux 3.2"},
        "gh": {"status": "missing"},
        "glab": {"status": "missing"},
        "codex": {"status": "missing"},
    }


class ReleaseMetadataTests(unittest.TestCase):
    def test_selects_official_github_deb(self) -> None:
        payload = {
            "tag_name": "v2.93.0",
            "assets": [
                {
                    "name": "gh_2.93.0_linux_amd64.deb",
                    "browser_download_url": "https://github.com/cli/cli/releases/download/v2.93.0/gh_2.93.0_linux_amd64.deb",
                    "digest": "sha256:" + "a" * 64,
                }
            ],
        }

        asset = system_tools.github_gh_asset(payload, "amd64")

        self.assertEqual(asset["name"], "gh_2.93.0_linux_amd64.deb")
        self.assertEqual(asset["digest"], "sha256:" + "a" * 64)

    def test_selects_official_gitlab_deb(self) -> None:
        payload = {
            "tag_name": "v1.115.0",
            "assets": {
                "links": [
                    {
                        "name": "glab_1.115.0_linux_amd64.deb",
                        "direct_asset_url": "https://gitlab.com/gitlab-org/cli/-/releases/v1.115.0/downloads/glab_1.115.0_linux_amd64.deb",
                    },
                    {
                        "name": "checksums.txt",
                        "direct_asset_url": "https://gitlab.com/gitlab-org/cli/-/releases/v1.115.0/downloads/checksums.txt",
                    },
                ]
            },
        }

        asset = system_tools.gitlab_glab_asset(payload, "amd64")

        self.assertEqual(asset["name"], "glab_1.115.0_linux_amd64.deb")
        self.assertEqual(
            asset["checksums_url"],
            "https://gitlab.com/gitlab-org/cli/-/releases/v1.115.0/downloads/checksums.txt",
        )

    def test_selects_exact_checksum(self) -> None:
        checksum = "a" * 64
        payload = f"{'b' * 64}  other.deb\n{checksum}  glab_1.115.0_linux_amd64.deb\n"

        selected = system_tools.checksum_for_asset(payload, "glab_1.115.0_linux_amd64.deb")

        self.assertEqual(selected, f"sha256:{checksum}")

    def test_rejects_duplicate_checksum(self) -> None:
        line = f"{'a' * 64}  glab_1.115.0_linux_amd64.deb"

        with self.assertRaises(SetupError) as raised:
            system_tools.checksum_for_asset(f"{line}\n{line}\n", "glab_1.115.0_linux_amd64.deb")

        self.assertEqual(raised.exception.code, "release_checksum_invalid")

    def test_rejects_untrusted_release_url(self) -> None:
        payload = {
            "tag_name": "v2.93.0",
            "assets": [
                {
                    "name": "gh_2.93.0_linux_amd64.deb",
                    "browser_download_url": "https://example.com/gh.deb",
                }
            ],
        }

        with self.assertRaises(SetupError) as raised:
            system_tools.github_gh_asset(payload, "amd64")

        self.assertEqual(raised.exception.code, "untrusted_download_url")

    def test_rejects_unexpected_release_tag(self) -> None:
        with self.assertRaises(SetupError) as raised:
            system_tools.release_version({"tag_name": "latest"})

        self.assertEqual(raised.exception.code, "release_tag_invalid")


class SystemInstallerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="system-tools-test-")
        self.home = Path(self.temporary.name) / "home"
        self.home.mkdir()
        self.reporter = Reporter(json_mode=False, command="tools")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_nvm_node_install_activates_returned_linux_bin(self) -> None:
        nvm_script = self.home / ".nvm/nvm.sh"
        nvm_script.parent.mkdir()
        nvm_script.write_text("# test\n", encoding="utf-8")
        node = self.home / ".nvm/versions/node/v22.19.0/bin/node"
        node.parent.mkdir(parents=True)
        node.write_text("", encoding="utf-8")
        completed = subprocess.CompletedProcess(
            args=["bash"],
            returncode=0,
            stdout=f"{node}\n",
            stderr="",
        )

        old_node_bin = self.home / ".nvm/versions/node/v20.19.4/bin"
        with mock.patch.dict(
            os.environ,
            {
                "PATH": f"{old_node_bin}{os.pathsep}/usr/bin",
                "NVM_DIR": os.fspath(nvm_script.parent),
            },
        ), mock.patch.object(
            system_tools.shutil,
            "which",
            return_value="/usr/bin/bash",
        ), mock.patch.object(
            system_tools,
            "run_checked",
            return_value=completed,
        ):
            system_tools.install_supported_node_with_nvm(self.home, self.reporter)
            self.assertEqual(os.environ["PATH"].split(os.pathsep)[0], os.fspath(node.parent))
            self.assertNotIn(os.fspath(old_node_bin), os.environ["PATH"].split(os.pathsep))

    def test_installs_missing_gh_and_glab_without_sudo(self) -> None:
        results = prerequisite_results()
        with mock.patch.object(system_tools, "authorize_sudo") as authorize, mock.patch.object(
            system_tools,
            "dpkg_architecture",
            return_value="amd64",
        ), mock.patch.object(
            system_tools,
            "install_release_package_user",
        ) as install:
            system_tools.install_wsl_prerequisites(self.home, results, self.reporter)

        authorize.assert_not_called()
        self.assertEqual(
            install.call_args_list,
            [
                mock.call("gh", "amd64", self.home, self.reporter),
                mock.call("glab", "amd64", self.home, self.reporter),
            ],
        )

    def test_installs_verified_package_binary_into_local_bin(self) -> None:
        asset = {
            "name": "gh_2.98.0_linux_amd64.deb",
            "url": "https://github.com/cli/cli/releases/download/v2.98.0/gh_2.98.0_linux_amd64.deb",
            "digest": "sha256:" + "a" * 64,
        }

        def extract_package(arguments: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
            extracted = Path(arguments[-1])
            binary = extracted / "usr/bin/gh"
            binary.parent.mkdir(parents=True)
            binary.write_text("#!/bin/sh\n", encoding="utf-8")
            return subprocess.CompletedProcess(arguments, 0, "", "")

        with mock.patch.object(system_tools, "fetch_json", return_value={}), mock.patch.object(
            system_tools,
            "github_gh_asset",
            return_value=asset,
        ), mock.patch.object(
            system_tools,
            "download_package",
            return_value="a" * 64,
        ), mock.patch.object(
            system_tools.shutil,
            "which",
            return_value="/usr/bin/dpkg-deb",
        ), mock.patch.object(
            system_tools,
            "run_checked",
            side_effect=extract_package,
        ), mock.patch.dict(
            os.environ,
            {"PATH": "/usr/bin"},
        ):
            system_tools.install_release_package_user("gh", "amd64", self.home, self.reporter)

            target = self.home / ".local/bin/gh"
            self.assertTrue(target.is_file())
            self.assertEqual(target.stat().st_mode & 0o777, 0o755)
            self.assertEqual(os.environ["PATH"].split(os.pathsep)[0], os.fspath(target.parent))

    def test_node_only_install_does_not_require_sudo(self) -> None:
        results = prerequisite_results()
        results["node"] = {"status": "missing"}
        results["npm"] = {"status": "missing"}
        results["gh"] = {"status": "ok", "path": "/usr/bin/gh", "version": "gh 2.98.0"}
        results["glab"] = {"status": "ok", "path": "/usr/bin/glab", "version": "glab 1.115.0"}

        with mock.patch.object(system_tools, "authorize_sudo") as authorize, mock.patch.object(
            system_tools,
            "install_supported_node_with_nvm",
        ) as install_node:
            system_tools.install_wsl_prerequisites(self.home, results, self.reporter)

        authorize.assert_not_called()
        install_node.assert_called_once_with(self.home, self.reporter)


if __name__ == "__main__":
    unittest.main()
