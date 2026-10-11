"""Integration checks against a temporary home; never apply to the real home."""

import json
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

    def secrets(self):
        codex = tomllib.loads((self.home / ".codex/config.toml").read_text())
        opencode = json.loads((self.home / ".config/opencode/config.json").read_text())
        cursor = json.loads((self.home / ".cursor/mcp.json").read_text())
        args = cursor["mcpServers"]["duckduckgo-mcp-server"]["args"]
        return (
            codex["mcp_servers"]["tmm_-tradermakemoney-"]["http_headers"][
                "Authorization"
            ],
            opencode["provider"]["customapi"]["options"]["apiKey"],
            args[args.index("--key") + 1],
        )

    def test_clean_restore_and_idempotence(self):
        self.chezmoi("apply")
        self.assertEqual(self.secrets(), ("", "", ""))
        self.assertIn(str(self.home), (self.home / ".zshrc").read_text())
        self.assertNotIn("/Users/akv", (self.home / ".codex/config.toml").read_text())
        for name in ("README.md", "Brewfile", "metadata", "tests", "scripts"):
            self.assertFalse((self.home / name).exists(), name)
        for name in (".hyper.js", ".gitconfig", ".codex/AGENTS.md"):
            self.assertTrue((self.home / name).is_file(), name)
        plist = self.home / "Library/Preferences/com.googlecode.iterm2.plist"
        if os.uname().sysname == "Darwin":
            self.assertTrue(plistlib.loads(plist.read_bytes())["New Bookmarks"])
        self.chezmoi("apply")
        self.chezmoi("verify")
        self.assertEqual(self.chezmoi("status").stdout, "")
        subprocess.run(["zsh", "-n", str(self.home / ".zshrc")], check=True)
        for name in (".bashrc", ".bash_profile", ".profile", ".local/bin/env"):
            subprocess.run(["bash", "-n", str(self.home / name)], check=True)

    def test_existing_secrets_survive_apply(self):
        self.write(
            ".codex/config.toml",
            "[mcp_servers.tmm_-tradermakemoney-.http_headers]\n"
            'Authorization = "local-codex-test-token"\n',
        )
        self.write(
            ".config/opencode/config.json",
            json.dumps(
                {
                    "provider": {
                        "customapi": {"options": {"apiKey": "local-opencode-test-key"}}
                    }
                }
            ),
        )
        self.write(
            ".cursor/mcp.json",
            json.dumps(
                {
                    "mcpServers": {
                        "duckduckgo-mcp-server": {
                            "args": ["--key", "local-cursor-test-key"]
                        }
                    }
                }
            ),
        )
        self.write(".config/unmanaged/settings", "keep me\n")
        self.chezmoi("apply", "--force")
        self.assertEqual(
            self.secrets(),
            (
                "local-codex-test-token",
                "local-opencode-test-key",
                "local-cursor-test-key",
            ),
        )
        self.assertEqual(
            (self.home / ".config/unmanaged/settings").read_text(), "keep me\n"
        )
        self.chezmoi("verify")

    def test_missing_secret_fields_are_supported(self):
        self.write(".codex/config.toml", 'model = "existing-model"\n')
        self.write(".config/opencode/config.json", "{}\n")
        self.write(".cursor/mcp.json", "{}\n")
        self.chezmoi("apply", "--force")
        self.assertEqual(self.secrets(), ("", "", ""))

    def test_invalid_local_config_fails_without_overwriting_it(self):
        path = ".codex/config.toml"
        self.write(path, "invalid toml [\n")
        result = self.chezmoi("apply", "--force", check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual((self.home / path).read_text(), "invalid toml [\n")


if __name__ == "__main__":
    unittest.main()
