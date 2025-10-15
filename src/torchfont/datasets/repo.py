import shutil
import subprocess
from collections.abc import Callable, Sequence
from pathlib import Path

from torchfont.datasets.folder import FontFolder


class FontRepo(FontFolder):
    def __init__(
        self,
        root: Path | str,
        url: str,
        ref: str,
        *,
        patterns: Sequence[str],
        codepoint_filter: Sequence[int] | None = None,
        transform: Callable[[dict[str, object]], dict[str, object]] | None = None,
        download: bool = False,
    ) -> None:
        self.root = Path(root).expanduser().resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.url = url
        self.ref = ref
        self.patterns = patterns

        git = shutil.which("git")
        if not git:
            msg = "git not found in PATH"
            raise RuntimeError(msg)

        def run(*args: str) -> None:
            subprocess.run([git, *args], check=True, cwd=self.root)

        def capture(*args: str) -> str:
            return subprocess.run(
                [git, *args],
                check=True,
                cwd=self.root,
                capture_output=True,
                text=True,
            ).stdout.strip()

        if not any(self.root.iterdir()):
            if not download:
                msg = (
                    f"repository not found at '{self.root}'. "
                    "use download=True to clone it"
                )
                raise FileNotFoundError(msg)
            subprocess.run(
                [
                    git,
                    "clone",
                    "--filter=blob:none",
                    "--no-checkout",
                    self.url,
                    str(self.root),
                ],
                check=True,
            )
        else:
            repo_root = Path(capture("rev-parse", "--show-toplevel")).resolve()
            if repo_root != self.root:
                msg = (
                    "git repository toplevel does not match: "
                    f"expected '{self.root}', found '{repo_root}'"
                )
                raise RuntimeError(msg)

            origin_url = capture("remote", "get-url", "origin")
            if origin_url != self.url:
                msg = (
                    "remote 'origin' URL does not match: "
                    f"expected '{self.url}', found '{origin_url}'"
                )
                raise RuntimeError(msg)

        if download:
            run("sparse-checkout", "init", "--no-cone")
            run("sparse-checkout", "set", "--", *self.patterns)
            run("fetch", "origin", self.ref, "--depth=1", "--filter=blob:none")
            run("switch", "--detach", "FETCH_HEAD")

        self.commit_hash = capture("rev-parse", "HEAD")

        super().__init__(
            root=self.root,
            codepoint_filter=codepoint_filter,
            transform=transform,
        )
