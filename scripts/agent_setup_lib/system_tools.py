"""Install WSL2-native system prerequisites from official release assets."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import shlex
import shutil
import subprocess
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from .common import Reporter, SetupError, path_is_within, require_safe_home
from .repositories import run_checked


GITHUB_RELEASE_API = "https://api.github.com/repos/cli/cli/releases/latest"
GITLAB_RELEASE_API = "https://gitlab.com/api/v4/projects/gitlab-org%2Fcli/releases/permalink/latest"
MAX_API_BYTES = 4 * 1024 * 1024
MAX_CHECKSUM_BYTES = 1024 * 1024
MAX_TOOL_PACKAGE_BYTES = 100 * 1024 * 1024
RELEASE_TAG_RE = re.compile(r"^v([0-9]+(?:\.[0-9]+){2}(?:[-+._A-Za-z0-9]*)?)$")
CHECKSUM_LINE_RE = re.compile(r"^([0-9A-Fa-f]{64})\s+\*?(.+)$")
WINDOWS_MOUNTED_EXECUTABLE_RE = re.compile(r"^/mnt/[A-Za-z]/")
MINIMUM_NODE_VERSION = (22, 19, 0)
NVM_NODE_SELECTOR = "22.19"
ALLOWED_DOWNLOAD_HOSTS = {
    "github.com",
    "objects.githubusercontent.com",
    "release-assets.githubusercontent.com",
    "gitlab.com",
    "storage.googleapis.com",
}


def _https_url(value: str, *, allowed_hosts: set[str]) -> str:
    parsed = urllib.parse.urlsplit(value)
    if parsed.scheme != "https" or not parsed.hostname or parsed.hostname.lower() not in allowed_hosts:
        raise SetupError("untrusted_download_url", f"Refusing untrusted download URL: {value}", exit_code=3)
    if parsed.username or parsed.password or parsed.fragment:
        raise SetupError("untrusted_download_url", f"Refusing malformed download URL: {value}", exit_code=3)
    return value


def _request(url: str) -> urllib.request.Request:
    return urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "agent-advance-setup/0.2",
        },
    )


def fetch_json(url: str, *, allowed_hosts: set[str]) -> dict[str, Any]:
    _https_url(url, allowed_hosts=allowed_hosts)
    try:
        with urllib.request.urlopen(_request(url), timeout=30) as response:
            final_url = response.geturl()
            _https_url(final_url, allowed_hosts=allowed_hosts)
            content_length = response.headers.get("Content-Length")
            if content_length and int(content_length) > MAX_API_BYTES:
                raise SetupError("release_metadata_too_large", "Release metadata exceeds the safety limit.", exit_code=3)
            payload = response.read(MAX_API_BYTES + 1)
    except SetupError:
        raise
    except (OSError, ValueError) as error:
        raise SetupError("release_metadata_failed", f"Cannot read release metadata from {url}", exit_code=3) from error
    if len(payload) > MAX_API_BYTES:
        raise SetupError("release_metadata_too_large", "Release metadata exceeds the safety limit.", exit_code=3)
    try:
        value = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise SetupError("release_metadata_invalid", f"Invalid release metadata from {url}", exit_code=3) from error
    if not isinstance(value, dict):
        raise SetupError("release_metadata_invalid", f"Release metadata is not an object: {url}", exit_code=3)
    return value


def fetch_text(url: str, *, allowed_hosts: set[str], limit: int = MAX_CHECKSUM_BYTES) -> str:
    _https_url(url, allowed_hosts=allowed_hosts)
    try:
        with urllib.request.urlopen(_request(url), timeout=30) as response:
            _https_url(response.geturl(), allowed_hosts=allowed_hosts)
            content_length = response.headers.get("Content-Length")
            if content_length and int(content_length) > limit:
                raise SetupError("text_download_too_large", "Downloaded text exceeds the safety limit.", exit_code=3)
            payload = response.read(limit + 1)
    except SetupError:
        raise
    except (OSError, ValueError) as error:
        raise SetupError("text_download_failed", f"Cannot download text from {url}", exit_code=3) from error
    if len(payload) > limit:
        raise SetupError("text_download_too_large", "Downloaded text exceeds the safety limit.", exit_code=3)
    try:
        return payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise SetupError("text_download_invalid", f"Downloaded text is not UTF-8: {url}", exit_code=3) from error


def release_version(payload: dict[str, Any]) -> tuple[str, str]:
    tag = payload.get("tag_name")
    if not isinstance(tag, str):
        raise SetupError("release_tag_invalid", "Release metadata has no valid tag_name.", exit_code=3)
    match = RELEASE_TAG_RE.fullmatch(tag)
    if not match:
        raise SetupError("release_tag_invalid", f"Refusing unexpected release tag: {tag!r}", exit_code=3)
    return tag, match.group(1)


def dpkg_architecture() -> str:
    dpkg = shutil.which("dpkg")
    if dpkg is None:
        raise SetupError("dpkg_missing", "dpkg is required to install Ubuntu release packages.", exit_code=3)
    completed = run_checked(
        [dpkg, "--print-architecture"],
        timeout=10,
        error_code="architecture_detection_failed",
    )
    architecture = completed.stdout.strip()
    if architecture not in {"amd64", "arm64"}:
        raise SetupError(
            "unsupported_architecture",
            f"Only amd64 and arm64 WSL2 architectures are supported: {architecture!r}",
            exit_code=3,
        )
    return architecture


def github_gh_asset(payload: dict[str, Any], architecture: str) -> dict[str, str | None]:
    tag, version = release_version(payload)
    expected_name = f"gh_{version}_linux_{architecture}.deb"
    assets = payload.get("assets")
    if not isinstance(assets, list):
        raise SetupError("release_asset_missing", f"GitHub CLI release {tag} has no assets list.", exit_code=3)
    for asset in assets:
        if not isinstance(asset, dict) or asset.get("name") != expected_name:
            continue
        url = asset.get("browser_download_url")
        if not isinstance(url, str):
            break
        _https_url(url, allowed_hosts=ALLOWED_DOWNLOAD_HOSTS)
        digest = asset.get("digest")
        if digest is not None and not isinstance(digest, str):
            digest = None
        return {"name": expected_name, "url": url, "digest": digest}
    raise SetupError("release_asset_missing", f"GitHub CLI release {tag} lacks {expected_name}.", exit_code=3)


def gitlab_glab_asset(payload: dict[str, Any], architecture: str) -> dict[str, str | None]:
    tag, version = release_version(payload)
    expected_name = f"glab_{version}_linux_{architecture}.deb"
    assets = payload.get("assets")
    links = assets.get("links") if isinstance(assets, dict) else None
    if not isinstance(links, list):
        raise SetupError("release_asset_missing", f"GitLab CLI release {tag} has no asset links.", exit_code=3)
    package_url: str | None = None
    checksums_url: str | None = None
    for asset in links:
        if not isinstance(asset, dict):
            continue
        name = asset.get("name")
        if name not in {expected_name, "checksums.txt"}:
            continue
        url = asset.get("direct_asset_url") or asset.get("url")
        if not isinstance(url, str):
            continue
        _https_url(url, allowed_hosts=ALLOWED_DOWNLOAD_HOSTS)
        if name == expected_name:
            package_url = url
        else:
            checksums_url = url
    if package_url is None:
        raise SetupError("release_asset_missing", f"GitLab CLI release {tag} lacks {expected_name}.", exit_code=3)
    if checksums_url is None:
        raise SetupError("release_checksum_missing", f"GitLab CLI release {tag} lacks checksums.txt.", exit_code=3)
    return {
        "name": expected_name,
        "url": package_url,
        "digest": None,
        "checksums_url": checksums_url,
    }


def checksum_for_asset(checksums: str, expected_name: str) -> str:
    matches: list[str] = []
    for raw_line in checksums.splitlines():
        match = CHECKSUM_LINE_RE.fullmatch(raw_line.strip())
        if match and match.group(2) == expected_name:
            matches.append(match.group(1).lower())
    if len(matches) != 1:
        raise SetupError(
            "release_checksum_invalid",
            f"Expected exactly one SHA-256 checksum for {expected_name}, found {len(matches)}.",
            exit_code=3,
        )
    return f"sha256:{matches[0]}"


def download_package(asset: dict[str, str | None], destination: Path) -> str:
    url = str(asset["url"])
    _https_url(url, allowed_hosts=ALLOWED_DOWNLOAD_HOSTS)
    digest = hashlib.sha256()
    total = 0
    try:
        with urllib.request.urlopen(_request(url), timeout=60) as response:
            _https_url(response.geturl(), allowed_hosts=ALLOWED_DOWNLOAD_HOSTS)
            content_length = response.headers.get("Content-Length")
            if content_length and int(content_length) > MAX_TOOL_PACKAGE_BYTES:
                raise SetupError("tool_package_too_large", f"Tool package exceeds 100 MiB: {asset['name']}", exit_code=3)
            with destination.open("xb") as output:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > MAX_TOOL_PACKAGE_BYTES:
                        raise SetupError("tool_package_too_large", f"Tool package exceeds 100 MiB: {asset['name']}", exit_code=3)
                    output.write(chunk)
                    digest.update(chunk)
    except SetupError:
        if destination.exists():
            destination.unlink()
        raise
    except (OSError, ValueError) as error:
        if destination.exists():
            destination.unlink()
        raise SetupError("tool_download_failed", f"Cannot download {asset['name']}", exit_code=3) from error
    with destination.open("rb") as package_handle:
        package_header = package_handle.read(8)
    if total == 0 or package_header != b"!<arch>\n":
        destination.unlink(missing_ok=True)
        raise SetupError("tool_package_invalid", f"Downloaded file is not a Debian package: {asset['name']}", exit_code=3)
    actual_digest = digest.hexdigest()
    expected_digest = asset.get("digest")
    if expected_digest:
        if not expected_digest.startswith("sha256:") or actual_digest != expected_digest.split(":", 1)[1].lower():
            destination.unlink(missing_ok=True)
            raise SetupError("tool_package_digest", f"SHA-256 verification failed for {asset['name']}", exit_code=3)
    return actual_digest


def authorize_sudo() -> str:
    sudo = shutil.which("sudo")
    if sudo is None:
        raise SetupError("sudo_missing", "sudo is required to install Ubuntu packages.", exit_code=3)
    try:
        completed = subprocess.run([sudo, "-v"], check=False, timeout=120)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise SetupError("sudo_authorization_failed", "Could not authorize sudo.", exit_code=3) from error
    if completed.returncode != 0:
        raise SetupError("sudo_authorization_failed", "sudo authorization was refused.", exit_code=3)
    return sudo


def apt_update(sudo: str) -> None:
    run_checked(
        [sudo, "-n", "apt-get", "update"],
        timeout=900,
        error_code="apt_update_failed",
    )


def apt_install(sudo: str, packages: list[str]) -> None:
    run_checked(
        [sudo, "-n", "apt-get", "install", "-y", "--no-install-recommends", *packages],
        timeout=1800,
        error_code="apt_install_failed",
    )


def install_release_package_user(
    name: str,
    architecture: str,
    home: Path,
    reporter: Reporter,
) -> None:
    home = require_safe_home(home)
    if name == "gh":
        payload = fetch_json(GITHUB_RELEASE_API, allowed_hosts={"api.github.com"})
        asset = github_gh_asset(payload, architecture)
    elif name == "glab":
        payload = fetch_json(GITLAB_RELEASE_API, allowed_hosts={"gitlab.com"})
        asset = gitlab_glab_asset(payload, architecture)
        checksums_url = str(asset["checksums_url"])
        checksums = fetch_text(checksums_url, allowed_hosts=ALLOWED_DOWNLOAD_HOSTS)
        asset["digest"] = checksum_for_asset(checksums, str(asset["name"]))
    else:
        raise SetupError("unknown_release_tool", f"No release installer for {name}.", exit_code=4)
    with tempfile.TemporaryDirectory(prefix=f"agent-setup-{name}-") as temporary:
        package = Path(temporary) / str(asset["name"])
        digest = download_package(asset, package)
        reporter.emit("OK", "tool_downloaded", f"Downloaded official {name} package {asset['name']}.", sha256=digest)
        extracted = Path(temporary) / "extracted"
        dpkg_deb = shutil.which("dpkg-deb")
        if dpkg_deb is None:
            raise SetupError("dpkg_deb_missing", "dpkg-deb is required to extract official CLI packages.", exit_code=3)
        run_checked(
            [dpkg_deb, "-x", os.fspath(package), os.fspath(extracted)],
            timeout=120,
            error_code="tool_package_extract_failed",
        )
        source = extracted / "usr/bin" / name
        if source.is_symlink() or not source.is_file() or not path_is_within(source.resolve(), extracted):
            raise SetupError(
                "tool_package_binary_invalid",
                f"Official package does not contain a safe usr/bin/{name} binary.",
                exit_code=3,
            )
        local_bin = (home / ".local/bin").resolve(strict=False)
        if not path_is_within(local_bin, home):
            raise SetupError("unsafe_local_bin", f"User-local bin must stay below the selected home: {local_bin}", exit_code=3)
        local_bin.mkdir(mode=0o755, parents=True, exist_ok=True)
        target = local_bin / name
        descriptor, staged_name = tempfile.mkstemp(prefix=f".{name}.", dir=local_bin)
        os.close(descriptor)
        staged = Path(staged_name)
        try:
            shutil.copyfile(source, staged)
            staged.chmod(0o755)
            os.replace(staged, target)
        finally:
            staged.unlink(missing_ok=True)
    local_bin_text = os.fspath(local_bin)
    current_path = os.environ.get("PATH", "")
    if local_bin_text not in current_path.split(os.pathsep):
        os.environ["PATH"] = f"{local_bin_text}{os.pathsep}{current_path}"
    reporter.emit("OK", "user_tool_installed", f"Installed WSL2-native {name} at {target}.")


def _result_needs_install(result: dict[str, Any]) -> bool:
    path = str(result.get("path", ""))
    return result.get("status") != "ok" or bool(path and WINDOWS_MOUNTED_EXECUTABLE_RE.match(path))


def _node_version(result: dict[str, Any]) -> tuple[int, int, int] | None:
    match = re.search(r"(?:^|\s)v?(\d+)\.(\d+)\.(\d+)(?:\s|$)", str(result.get("version", "")))
    return tuple(int(part) for part in match.groups()) if match else None


def install_supported_node_with_nvm(home: Path, reporter: Reporter) -> None:
    home = require_safe_home(home)
    configured = os.environ.get("NVM_DIR")
    nvm_directory = Path(configured).expanduser() if configured else home / ".nvm"
    nvm_directory = nvm_directory.resolve(strict=False)
    if not path_is_within(nvm_directory, home):
        raise SetupError("unsafe_nvm_directory", f"NVM_DIR must be below the selected home: {nvm_directory}", exit_code=3)
    nvm_script = nvm_directory / "nvm.sh"
    if not nvm_script.is_file():
        raise SetupError(
            "nvm_missing",
            f"Node {NVM_NODE_SELECTOR} or newer is required and NVM was not found at {nvm_script}. Install NVM first.",
            exit_code=3,
        )
    bash = shutil.which("bash")
    if bash is None:
        raise SetupError("bash_missing", "bash is required to activate NVM.", exit_code=3)
    command = (
        f"source {shlex.quote(os.fspath(nvm_script))}; "
        f"nvm install {NVM_NODE_SELECTOR}; "
        f"nvm alias default {NVM_NODE_SELECTOR}; "
        f"nvm use {NVM_NODE_SELECTOR} >/dev/null; "
        f"nvm which {NVM_NODE_SELECTOR}"
    )
    completed = run_checked(
        [bash, "--noprofile", "--norc", "-c", command],
        timeout=1800,
        error_code="node_install_failed",
    )
    candidates = [Path(line.strip()) for line in completed.stdout.splitlines() if line.strip().startswith("/")]
    node = candidates[-1] if candidates else Path()
    if not node.is_file() or node.name != "node" or not path_is_within(node, nvm_directory):
        raise SetupError(
            "node_install_invalid",
            f"NVM did not return a safe Node {NVM_NODE_SELECTOR} executable.",
            exit_code=3,
        )
    node_bin = os.fspath(node.parent)
    versions_root = (nvm_directory / "versions/node").resolve(strict=False)
    current_entries = os.environ.get("PATH", "").split(os.pathsep)
    retained_entries = [
        entry
        for entry in current_entries
        if entry and not path_is_within(Path(entry).resolve(strict=False), versions_root)
    ]
    current_path = os.pathsep.join(retained_entries)
    os.environ["PATH"] = f"{node_bin}{os.pathsep}{current_path}"
    os.environ["NVM_BIN"] = node_bin
    reporter.emit("OK", "node_installed", f"Activated Node {NVM_NODE_SELECTOR} from {node_bin}.")


def install_wsl_prerequisites(
    home: Path,
    results: dict[str, dict[str, Any]],
    reporter: Reporter,
) -> None:
    if os.name != "posix" or platform.system() != "Linux":
        raise SetupError("unsupported_platform", "Automatic prerequisite installation supports WSL2/Linux only.")
    system_packages: list[str] = []
    for command, package in (("git", "git"), ("tmux", "tmux")):
        if _result_needs_install(results[command]):
            system_packages.append(package)
    node = results["node"]
    npm = results["npm"]
    installed_node_version = _node_version(node)
    install_node = (
        _result_needs_install(node)
        or _result_needs_install(npm)
        or installed_node_version is None
        or installed_node_version < MINIMUM_NODE_VERSION
    )
    install_gh = _result_needs_install(results["gh"])
    install_glab = _result_needs_install(results["glab"])
    needs_apt = bool(system_packages)
    if not install_node and not needs_apt and not install_gh and not install_glab:
        reporter.emit("OK", "system_prerequisites", "WSL2 system prerequisites are already installed.")
        return

    sudo = authorize_sudo() if needs_apt else None
    if install_node:
        install_supported_node_with_nvm(home, reporter)
    if sudo is not None:
        apt_update(sudo)
        apt_install(sudo, system_packages)
        reporter.emit("OK", "system_packages_installed", f"Installed: {', '.join(system_packages)}.")
    if install_gh or install_glab:
        architecture = dpkg_architecture()
        if install_gh:
            install_release_package_user("gh", architecture, home, reporter)
        if install_glab:
            install_release_package_user("glab", architecture, home, reporter)
    reporter.emit("OK", "system_prerequisites", "WSL2 system prerequisites are ready.")
