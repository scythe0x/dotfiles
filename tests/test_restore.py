"""Integration checks against a temporary home; never apply to the real home."""

import os
import plistlib
import subprocess
import tempfile
import tomllib
import unittest
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1]


class RestoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.home = self.root / "home"
        self.home.mkdir()

    def chezmoi(self, *args, check=True):
        return subprocess.run(
            [
                "chezmoi",
                "--config",
                str(self.root / "empty.toml"),
                "--source",
                str(SOURCE),
                "--destination",
                str(self.home),
                "--cache",
                str(self.root / "cache"),
                "--persistent-state",
                str(self.root / "state.boltdb"),
                "--no-tty",
                *args,
            ],
            capture_output=True,
            text=True,
            check=check,
        )

    def write(self, name, text):
        path = self.home / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def secrets(self) -> str:
        codex = tomllib.loads((self.home / ".codex/config.toml").read_text())
        return codex["mcp_servers"]["tmm_-tradermakemoney-"]["http_headers"][
            "Authorization"
        ]

    def test_clean_restore_and_idempotence(self):
        self.chezmoi("apply")
        self.assertEqual(self.secrets(), "")
        self.assertIn("$HOME/.bun", (self.home / ".zshrc").read_text())
        self.assertNotIn("/Users/akv", (self.home / ".codex/config.toml").read_text())
        for name in (
            "README.md",
            "Brewfile",
            "metadata",
            "tests",
            "scripts",
            "install.sh",
        ):
            self.assertFalse((self.home / name).exists(), name)
        for name in (".zshrc", ".zprofile", ".gitconfig", ".codex/config.toml"):
            self.assertTrue((self.home / name).is_file(), name)
        plist = self.home / "Library/Preferences/com.googlecode.iterm2.plist"
        if os.uname().sysname == "Darwin":
            self.assertTrue(plistlib.loads(plist.read_bytes())["New Bookmarks"])
        self.chezmoi("apply")
        self.chezmoi("verify")
        self.assertEqual(self.chezmoi("status").stdout, "")
        subprocess.run(["zsh", "-n", str(self.home / ".zshrc")], check=True)
        subprocess.run(["zsh", "-n", str(self.home / ".zprofile")], check=True)
        for name in (
            ".config",
            ".hyper.js",
            ".ideavimrc",
            ".yarnrc",
            ".taskrc",
            ".nuxtrc",
            ".warp",
            ".local",
            ".bashrc",
            ".bash_profile",
            ".profile",
            ".cursor",
            ".vscode",
            ".codex/skills",
            ".codex/AGENTS.md",
        ):
            self.assertFalse((self.home / name).exists(), name)

    def test_existing_secrets_survive_apply(self):
        self.write(
            ".codex/config.toml",
            "[mcp_servers.tmm_-tradermakemoney-.http_headers]\n"
            'Authorization = "local-codex-test-token"\n',
        )
        self.write(".config/unmanaged/settings", "keep me\n")
        self.chezmoi("apply", "--force")
        self.assertEqual(self.secrets(), "local-codex-test-token")
        self.assertEqual(
            (self.home / ".config/unmanaged/settings").read_text(), "keep me\n"
        )
        self.chezmoi("verify")

    def test_missing_secret_fields_are_supported(self):
        self.write(".codex/config.toml", 'model = "existing-model"\n')
        self.chezmoi("apply", "--force")
        self.assertEqual(self.secrets(), "")

    def test_init_sets_source_directory(self):
        config = self.root / "generated.toml"
        self.chezmoi("init", "--config-path", str(config))
        self.assertEqual(tomllib.loads(config.read_text())["sourceDir"], str(SOURCE))

    def test_invalid_local_config_fails_without_overwriting_it(self):
        path = ".codex/config.toml"
        self.write(path, "invalid toml [\n")
        result = self.chezmoi("apply", "--force", check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual((self.home / path).read_text(), "invalid toml [\n")


if __name__ == "__main__":
    unittest.main()
