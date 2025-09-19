import shutil
import subprocess
from pathlib import Path
from typing import Callable

from torchfont.datasets.folder import FontFolder


class FontRepo(FontFolder):
    def __init__(
        self,
        root: Path | str,
        url: str,
        ref: str,
        patterns: list[str],
        codepoint_filter: list[int] | None = None,
        transform: Callable | None = None,
        download: bool = False,
    ) -> None:
        if shutil.which("git") is None:
            raise RuntimeError("Git is not installed or not found in PATH.")

        self.root = Path(root).expanduser().resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.url = url
        self.ref = ref
        self.patterns = patterns

        if download:
            self._sync_repo()

        self.commit_hash = self._read_commit_hash()

        super().__init__(
            root=self.root,
            codepoint_filter=codepoint_filter,
            transform=transform,
        )

    def _sync_repo(self) -> None:
        repo = str(self.root)

        if not (self.root / ".git").exists():
            subprocess.run(
                [
                    "git",
                    "clone",
                    "--filter=blob:none",
                    "--sparse",
                    "--no-checkout",
                    self.url,
                    repo,
                ],
                check=True,
            )

        subprocess.run(
            ["git", "-C", repo, "sparse-checkout", "init", "--no-cone"],
            check=True,
        )
        subprocess.run(
            ["git", "-C", repo, "sparse-checkout", "set", "--", *self.patterns],
            check=True,
        )
        subprocess.run(
            [
                "git",
                "-C",
                repo,
                "fetch",
                "origin",
                self.ref,
                "--depth=1",
                "--filter=blob:none",
            ],
            check=True,
        )
        subprocess.run(
            ["git", "-C", repo, "switch", "--detach", "FETCH_HEAD"],
            check=True,
        )

    def _read_commit_hash(self) -> str:
        if not (self.root / ".git").exists():
            raise FileNotFoundError("Repository not found. Set download=True to fetch.")

        out = subprocess.run(
            ["git", "-C", str(self.root), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )

        return out.stdout.strip()
