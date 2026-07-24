#!/usr/bin/env python3
"""Validate the Karnel registry without executing plugin code."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "registry.json"
SCHEMA_PATHS = (
    ROOT / "schemas" / "registry.schema.json",
    ROOT / "schemas" / "karnel-plugin.schema.json",
)
SEMVER_IDENTIFIER = r"(?:0|[1-9][0-9]*|[0-9A-Za-z-]*[A-Za-z-][0-9A-Za-z-]*)"
SEMVER_RE = re.compile(
    r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"
    rf"(?:-({SEMVER_IDENTIFIER}(?:\.{SEMVER_IDENTIFIER})*))?"
    r"(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"
)
NAME_RE = re.compile(r"^[a-z][a-z0-9-]{0,62}$")
REPO_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9-]{0,38}/[A-Za-z0-9][A-Za-z0-9._-]{0,99}$")
REF_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]{0,127}$")
PATH_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]{0,127}$")
CHECKSUM_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
LICENSE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9.-]{0,63}$")
CAPABILITIES = {
    "network",
    "filesystem-read",
    "filesystem-write",
    "process",
    "environment",
}
MANIFEST_REQUIRED = {
    "schemaVersion",
    "name",
    "version",
    "description",
    "commands",
    "minKarnelVersion",
    "license",
}
MANIFEST_ALLOWED = MANIFEST_REQUIRED | {"checksum", "capabilities"}
ENTRY_REQUIRED = {
    "name",
    "repo",
    "ref",
    "version",
    "description",
    "commands",
    "minKarnelVersion",
    "license",
    "checksum",
}
ENTRY_ALLOWED = ENTRY_REQUIRED | {"commit", "path", "capabilities"}


class Validator:
    def __init__(self, require_shellcheck: bool, native_commands: set[str]) -> None:
        self.errors: list[str] = []
        self.require_shellcheck = require_shellcheck
        self.native_commands = native_commands

    def fail(self, message: str) -> None:
        self.errors.append(message)

    def load_json(self, path: Path) -> Any | None:
        try:
            with path.open(encoding="utf-8") as file:
                return json.load(file)
        except (OSError, json.JSONDecodeError) as error:
            self.fail(f"{path}: invalid JSON: {error}")
            return None

    def require_regular_file(self, root: Path, path: Path, label: str) -> bool:
        if path.is_symlink() or not path.is_file():
            self.fail(f"{label}: must be a regular file")
            return False
        return self.require_inside(root, path, label)

    def require_inside(self, root: Path, path: Path, label: str) -> bool:
        try:
            path.resolve(strict=True).relative_to(root.resolve(strict=True))
        except (OSError, ValueError):
            self.fail(f"{label}: escapes the plugin directory")
            return False
        return True

    def validate_description(self, value: Any, label: str) -> bool:
        if not isinstance(value, str) or not value or len(value) > 160:
            self.fail(f"{label}: description must be a non-empty string up to 160 characters")
            return False
        if any(ord(character) < 32 or ord(character) == 127 for character in value):
            self.fail(f"{label}: description must be a single line")
            return False
        return True

    def validate_commands(self, value: Any, label: str) -> list[str] | None:
        if not isinstance(value, list) or not value:
            self.fail(f"{label}: commands must be a non-empty array")
            return None
        if not all(isinstance(command, str) and NAME_RE.fullmatch(command) for command in value):
            self.fail(f"{label}: commands contain an invalid name")
            return None
        if len(value) != len(set(value)):
            self.fail(f"{label}: commands contain duplicates")
            return None
        return value

    def validate_capabilities(self, value: Any, label: str) -> bool:
        if value is None:
            return True
        if not isinstance(value, list):
            self.fail(f"{label}: capabilities must be an array")
            return False
        if any(not isinstance(capability, str) or capability not in CAPABILITIES for capability in value):
            self.fail(f"{label}: capabilities contain an unsupported declaration")
            return False
        if len(value) != len(set(value)):
            self.fail(f"{label}: capabilities must be unique")
            return False
        return True

    def validate_plugin_symlinks(self, plugin_dir: Path) -> None:
        for base, directories, files in os.walk(plugin_dir, followlinks=False):
            if ".git" in directories:
                directories.remove(".git")
            for name in [*directories, *files]:
                path = Path(base) / name
                if path.is_symlink():
                    self.fail(f"{path}: plugin payload must not contain symbolic links")

    def payload_checksum(self, plugin_dir: Path) -> str | None:
        files: list[Path] = []
        for base, directories, filenames in os.walk(plugin_dir, followlinks=False):
            if ".git" in directories:
                directories.remove(".git")
            for name in filenames:
                path = Path(base) / name
                if path.is_symlink() or not path.is_file():
                    continue
                relative = path.relative_to(plugin_dir).as_posix()
                if relative in {"karnel-plugin.json", ".karnel-install.json"}:
                    continue
                files.append(path)

        digest = hashlib.sha256()
        try:
            for path in sorted(files, key=lambda item: item.relative_to(plugin_dir).as_posix().encode()):
                relative = path.relative_to(plugin_dir).as_posix().encode()
                file_hash = hashlib.sha256(path.read_bytes()).hexdigest().encode()
                digest.update(relative)
                digest.update(b"\0")
                digest.update(file_hash)
                digest.update(b"\0")
        except OSError as error:
            self.fail(f"{plugin_dir}: cannot calculate payload checksum: {error}")
            return None
        return "sha256:" + digest.hexdigest()

    def validate_manifest(self, plugin_dir: Path, entry: dict[str, Any]) -> None:
        label = str(plugin_dir)
        if plugin_dir.is_symlink() or not plugin_dir.is_dir():
            self.fail(f"{label}: plugin directory must be a regular directory")
            return
        self.validate_plugin_symlinks(plugin_dir)

        manifest_path = plugin_dir / "karnel-plugin.json"
        if not self.require_regular_file(plugin_dir, manifest_path, f"{label}/karnel-plugin.json"):
            return
        manifest = self.load_json(manifest_path)
        if not isinstance(manifest, dict):
            self.fail(f"{label}: manifest must be a JSON object")
            return

        unknown = set(manifest) - MANIFEST_ALLOWED
        missing = MANIFEST_REQUIRED - set(manifest)
        if unknown:
            self.fail(f"{label}: manifest has unknown fields: {', '.join(sorted(unknown))}")
        if missing:
            self.fail(f"{label}: manifest is missing fields: {', '.join(sorted(missing))}")
        if unknown or missing:
            return

        if manifest.get("schemaVersion") != 1:
            self.fail(f"{label}: manifest schemaVersion must be 1")
        if not isinstance(manifest.get("name"), str) or not NAME_RE.fullmatch(manifest["name"]):
            self.fail(f"{label}: manifest name is invalid")
        if not isinstance(manifest.get("version"), str) or not SEMVER_RE.fullmatch(manifest["version"]):
            self.fail(f"{label}: manifest version is not SemVer")
        self.validate_description(manifest.get("description"), label)
        commands = self.validate_commands(manifest.get("commands"), label)
        if not isinstance(manifest.get("minKarnelVersion"), str) or not SEMVER_RE.fullmatch(manifest["minKarnelVersion"]):
            self.fail(f"{label}: manifest minKarnelVersion is not SemVer")
        if not isinstance(manifest.get("license"), str) or not LICENSE_RE.fullmatch(manifest["license"]):
            self.fail(f"{label}: manifest license is invalid")
        if "checksum" in manifest and (
            not isinstance(manifest["checksum"], str) or not CHECKSUM_RE.fullmatch(manifest["checksum"])
        ):
            self.fail(f"{label}: manifest checksum is invalid")
        self.validate_capabilities(manifest.get("capabilities"), label)

        if commands is not None:
            self.validate_command_files(plugin_dir, commands)

        license_path = plugin_dir / "LICENSE"
        if not license_path.exists():
            license_path = plugin_dir / "LICENSE.md"
        self.require_regular_file(plugin_dir, license_path, f"{label}/LICENSE")

        if manifest.get("checksum") is not None:
            actual_checksum = self.payload_checksum(plugin_dir)
            if actual_checksum is not None and manifest["checksum"] != actual_checksum:
                self.fail(f"{label}: payload checksum does not match manifest")

        for field in (
            "name",
            "version",
            "description",
            "commands",
            "minKarnelVersion",
            "license",
            "checksum",
        ):
            if manifest.get(field) != entry.get(field):
                self.fail(f"{label}: manifest {field} does not match registry entry")
        if manifest.get("capabilities", []) != entry.get("capabilities", []):
            self.fail(f"{label}: manifest capabilities do not match registry entry")

    def validate_command_files(self, plugin_dir: Path, commands: list[str]) -> None:
        commands_dir = plugin_dir / "commands"
        label = str(plugin_dir)
        if commands_dir.is_symlink() or not commands_dir.is_dir() or not self.require_inside(plugin_dir, commands_dir, f"{label}/commands"):
            self.fail(f"{label}: commands must be a regular directory inside the plugin")
            return

        discovered: set[str] = set()
        for command in commands:
            command_path = commands_dir / f"{command}.sh"
            if not self.require_regular_file(plugin_dir, command_path, f"{label}/commands/{command}.sh"):
                continue
            discovered.add(command)
            self.run_static_checks(command_path, command)

        actual_files: set[str] = set()
        for path in commands_dir.glob("*.sh"):
            if path.is_symlink() or not path.is_file():
                self.fail(f"{path}: command entry must be a regular file")
                continue
            actual_files.add(path.stem)
        unexpected = actual_files - set(commands)
        if unexpected:
            self.fail(f"{label}: commands contains undeclared files: {', '.join(sorted(unexpected))}")
        if discovered != set(commands):
            return

    def run_static_checks(self, command_path: Path, command_name: str) -> None:
        syntax = subprocess.run(["bash", "-n", str(command_path)], capture_output=True, text=True)
        if syntax.returncode:
            self.fail(f"{command_path}: Bash syntax error: {syntax.stderr.strip()}")
        handler = re.compile(
            rf"^[ \t]*(?:function[ \t]+)?{re.escape(command_name)}_main[ \t]*(?:\([ \t]*\))?[ \t]*\{{",
            re.MULTILINE,
        )
        try:
            if not handler.search(command_path.read_text(encoding="utf-8")):
                self.fail(f"{command_path}: must define {command_name}_main")
        except (OSError, UnicodeDecodeError) as error:
            self.fail(f"{command_path}: cannot read command: {error}")
        shellcheck = shutil.which("shellcheck")
        if self.require_shellcheck and shellcheck is None:
            self.fail("shellcheck is required for registry validation")
            return
        if shellcheck is not None:
            result = subprocess.run(
                [shellcheck, "--shell=bash", "--severity=error", str(command_path)],
                capture_output=True,
                text=True,
            )
            if result.returncode:
                self.fail(f"{command_path}: ShellCheck failed: {result.stdout}{result.stderr}".strip())

    def validate_entry(self, entry: Any, index: int) -> dict[str, Any] | None:
        label = f"registry.plugins[{index}]"
        error_count = len(self.errors)
        if not isinstance(entry, dict):
            self.fail(f"{label}: entry must be an object")
            return None
        unknown = set(entry) - ENTRY_ALLOWED
        missing = ENTRY_REQUIRED - set(entry)
        if unknown:
            self.fail(f"{label}: unknown fields: {', '.join(sorted(unknown))}")
        if missing:
            self.fail(f"{label}: missing fields: {', '.join(sorted(missing))}")
        if unknown or missing:
            return None

        if not isinstance(entry["name"], str) or not NAME_RE.fullmatch(entry["name"]):
            self.fail(f"{label}: name is invalid")
        repo = entry["repo"]
        if not isinstance(repo, str) or not REPO_RE.fullmatch(repo) or ".." in repo or repo.endswith(".git"):
            self.fail(f"{label}: repo must be exactly owner/repo")
        ref = entry["ref"]
        if not isinstance(ref, str) or not REF_RE.fullmatch(ref) or ".." in ref or "//" in ref or ref.endswith("/"):
            self.fail(f"{label}: ref is invalid")
        if "path" in entry:
            path = entry["path"]
            if not isinstance(path, str) or not PATH_RE.fullmatch(path) or ".." in path or "//" in path or path.endswith("/") or path.startswith(".git"):
                self.fail(f"{label}: path is invalid")
        if "commit" in entry and (not isinstance(entry["commit"], str) or not re.fullmatch(r"[0-9a-f]{40}", entry["commit"])):
            self.fail(f"{label}: commit must be a full lowercase SHA-1")
        if not isinstance(entry["version"], str) or not SEMVER_RE.fullmatch(entry["version"]):
            self.fail(f"{label}: version is not SemVer")
        self.validate_description(entry["description"], label)
        self.validate_commands(entry["commands"], label)
        if not isinstance(entry["minKarnelVersion"], str) or not SEMVER_RE.fullmatch(entry["minKarnelVersion"]):
            self.fail(f"{label}: minKarnelVersion is not SemVer")
        if not isinstance(entry["license"], str) or not LICENSE_RE.fullmatch(entry["license"]):
            self.fail(f"{label}: license is invalid")
        if not isinstance(entry["checksum"], str) or not CHECKSUM_RE.fullmatch(entry["checksum"]):
            self.fail(f"{label}: checksum is invalid")
        self.validate_capabilities(entry.get("capabilities"), label)
        return entry if len(self.errors) == error_count else None

    def validate_registry(self, registry: Any) -> list[dict[str, Any]]:
        if not isinstance(registry, dict):
            self.fail("registry: root must be an object")
            return []
        expected_keys = {"schemaVersion", "description", "plugins"}
        if set(registry) != expected_keys:
            self.fail("registry: unknown or missing top-level fields")
            return []
        if registry["schemaVersion"] != 1:
            self.fail("registry: schemaVersion must be 1")
        if not isinstance(registry["description"], str) or not registry["description"]:
            self.fail("registry: description must be a non-empty string")
        if not isinstance(registry["plugins"], list):
            self.fail("registry: plugins must be an array")
            return []

        entries = [self.validate_entry(entry, index) for index, entry in enumerate(registry["plugins"])]
        valid_entries = [entry for entry in entries if entry is not None]
        names = [entry["name"] for entry in valid_entries]
        repos = [entry["repo"] for entry in valid_entries]
        if len(names) != len(set(names)):
            self.fail("registry: plugin names must be unique")
        if len(repos) != len(set(repos)):
            self.fail("registry: plugin repositories must be unique")
        command_owners: dict[str, str] = {}
        native_commands = self.native_commands | {"karnel"}
        for entry in valid_entries:
            for command in entry["commands"]:
                if command in native_commands:
                    self.fail(f"registry: command '{command}' collides with a native Karnel command")
                owner = command_owners.get(command)
                if owner is not None:
                    self.fail(f"registry: command '{command}' is declared by both '{owner}' and '{entry['name']}'")
                command_owners[command] = entry["name"]
        return valid_entries

    def validate_remote_entry(self, entry: dict[str, Any]) -> None:
        with tempfile.TemporaryDirectory(prefix="karnel-registry-") as temporary:
            checkout = Path(temporary) / "repository"
            command = [
                "git",
                "clone",
                "--depth=1",
                "--branch",
                entry["ref"],
                f"https://github.com/{entry['repo']}.git",
                str(checkout),
            ]
            clone = subprocess.run(command, capture_output=True, text=True)
            if clone.returncode:
                self.fail(f"{entry['name']}: repository is not accessible at {entry['repo']}@{entry['ref']}: {clone.stderr.strip()}")
                return
            commit = subprocess.run(
                ["git", "-C", str(checkout), "rev-parse", "HEAD"], capture_output=True, text=True
            )
            if commit.returncode:
                self.fail(f"{entry['name']}: cannot resolve fetched commit")
                return
            if "commit" in entry and commit.stdout.strip() != entry["commit"]:
                self.fail(f"{entry['name']}: fetched commit does not match registry commit")
            plugin_dir = checkout / entry.get("path", ".")
            if not self.require_inside(checkout, plugin_dir, f"{entry['name']}: plugin path"):
                return
            self.validate_manifest(plugin_dir, entry)

    def validate_local_entry(self, entry: dict[str, Any]) -> None:
        plugin_dir = ROOT / entry.get("path", ".")
        if not self.require_inside(ROOT, plugin_dir, f"{entry['name']}: local plugin path"):
            return
        if "commit" in entry:
            commit = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True)
            if commit.returncode:
                self.fail(f"{entry['name']}: cannot resolve local repository commit")
            elif commit.stdout.strip() != entry["commit"]:
                self.fail(f"{entry['name']}: local commit does not match registry commit")
        self.validate_manifest(plugin_dir, entry)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offline", action="store_true", help="Validate JSON and registry semantics without cloning repositories.")
    parser.add_argument("--require-shellcheck", action="store_true", help="Fail if ShellCheck is unavailable.")
    parser.add_argument("--local-repository", help="Validate entries for this owner/repo from the checked-out repository.")
    parser.add_argument("--native-commands-dir", type=Path, help="Directory containing native Karnel command .sh files.")
    arguments = parser.parse_args()

    native_commands: set[str] = set()
    if arguments.native_commands_dir is not None:
        if not arguments.native_commands_dir.is_dir():
            print(f"ERROR: native commands directory does not exist: {arguments.native_commands_dir}", file=sys.stderr)
            return 1
        native_commands = {
            path.stem
            for path in arguments.native_commands_dir.glob("*.sh")
            if path.is_file() and not path.is_symlink()
        }

    validator = Validator(require_shellcheck=arguments.require_shellcheck, native_commands=native_commands)
    for schema_path in SCHEMA_PATHS:
        validator.load_json(schema_path)
    registry = validator.load_json(REGISTRY_PATH)
    entries = validator.validate_registry(registry) if registry is not None else []
    if not arguments.offline:
        for entry in entries:
            if arguments.local_repository == entry["repo"]:
                validator.validate_local_entry(entry)
            else:
                validator.validate_remote_entry(entry)

    if validator.errors:
        for error in validator.errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"Registry validation passed ({len(entries)} plugin(s)).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
