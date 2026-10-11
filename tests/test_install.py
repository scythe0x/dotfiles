"""run the installer with fake external tools; no system changes or network."""

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1]


class InstallTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.log = self.root / "calls"
        self.env = {
            **os.environ,
            "HOME": str(self.root / "home with spaces"),
            "PATH": f"{self.bin}:/usr/bin:/bin",
            "DOTFILES_TEST_LOG": str(self.log),
            "DOTFILES_TEST_BIN": str(self.bin),
        }
        self.tool("uname", 'printf "%s\\n" "${DOTFILES_TEST_OS:-Darwin}"')
        self.tool(
            "brew",
            """printf 'brew %s\n' "$*" >> "$DOTFILES_TEST_LOG"
if [[ "${DOTFILES_TEST_FAIL:-}" == "$1" ]]; then exit 1; fi
if [[ "$1" == shellenv ]]; then
    printf 'export PATH=%q:$PATH\n' "$DOTFILES_TEST_BIN"
elif [[ "$1" == bundle ]]; then
    [[ "$2" == install && "$3" == "--file=$HOME/projects/dotfiles/Brewfile" && "$4" == --no-upgrade ]]
    [[ -f "$HOME/projects/dotfiles/Brewfile" ]]
fi""",
        )
        self.tool(
            "chezmoi",
            """printf 'chezmoi %s\n' "$*" >> "$DOTFILES_TEST_LOG"
[[ "$1" == --source && "$2" == "$HOME/projects/dotfiles" ]]
if [[ "${DOTFILES_TEST_FAIL:-}" == "$3" ]]; then exit 1; fi
if [[ "$3" == init ]]; then
    [[ "$4" == https://github.com/scythe0x/dotfiles.git ]]
    mkdir -p "$2"
    touch "$2/Brewfile"
fi""",
        )
        self.tool(
            "curl",
            """printf 'curl %s\n' "$*" >> "$DOTFILES_TEST_LOG"
if [[ "${DOTFILES_TEST_FAIL:-}" == curl ]]; then exit 22; fi
printf '%s\n' 'printf "homebrew install\\n" >> "$DOTFILES_TEST_LOG"; touch "$DOTFILES_TEST_BIN/installed"' """,
        )

    def tool(self, name: str, body: str) -> None:
        path = self.bin / name
        path.write_text("#!/bin/bash\nset -euo pipefail\n" + body + "\n")
        path.chmod(0o755)

    def run_installer(
        self, *, missing_brew: bool = False
    ) -> subprocess.CompletedProcess[str]:
        if missing_brew:
            command = """source "$1"
find_brew() {
    [[ -f "$DOTFILES_TEST_BIN/installed" ]] || return 1
    printf '%s\n' "$DOTFILES_TEST_BIN/brew"
}
main"""
            args = [
                "/bin/bash",
                "-c",
                command,
                "test-install",
                str(SOURCE / "install.sh"),
            ]
        else:
            args = ["/bin/bash", str(SOURCE / "install.sh")]
        return subprocess.run(
            args, env=self.env, capture_output=True, text=True, check=False
        )

    def calls(self) -> list[str]:
        return self.log.read_text().splitlines() if self.log.exists() else []

    def test_existing_brew_and_repeat_install(self) -> None:
        for _ in range(2):
            result = self.run_installer()
            self.assertEqual(result.returncode, 0, result.stderr)
        calls = self.calls()
        self.assertEqual(len(calls), 10)
        self.assertEqual(calls[:5], calls[5:])
        self.assertEqual(calls[0], "brew shellenv")
        self.assertEqual(calls[1], "brew install chezmoi")
        self.assertIn(" init https://github.com/scythe0x/dotfiles.git", calls[2])
        self.assertTrue(calls[3].startswith("brew bundle install "))
        self.assertTrue(calls[4].endswith(" apply"))

    def test_missing_brew_runs_official_installer_first(self) -> None:
        result = self.run_installer(missing_brew=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            self.calls()[:3],
            [
                "curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh",
                "homebrew install",
                "brew shellenv",
            ],
        )

    def test_script_runs_as_downloaded_inline_command(self) -> None:
        result = subprocess.run(
            ["/bin/bash", "-c", (SOURCE / "install.sh").read_text()],
            env=self.env,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(self.calls()[-1].endswith(" apply"))

    def test_failures_stop_before_applying(self) -> None:
        for stage in ("shellenv", "install", "init", "bundle"):
            with self.subTest(stage=stage):
                self.log.unlink(missing_ok=True)
                self.env["DOTFILES_TEST_FAIL"] = stage
                result = self.run_installer()
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse(any(line.endswith(" apply") for line in self.calls()))
                self.assertNotIn("done.", result.stdout)

    def test_download_failure_does_not_run_homebrew_installer(self) -> None:
        self.env["DOTFILES_TEST_FAIL"] = "curl"
        result = self.run_installer(missing_brew=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(len(self.calls()), 1)

    def test_unsupported_os_does_not_install_anything(self) -> None:
        self.env["DOTFILES_TEST_OS"] = "Linux"
        result = self.run_installer()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.calls(), [])


if __name__ == "__main__":
    unittest.main()
