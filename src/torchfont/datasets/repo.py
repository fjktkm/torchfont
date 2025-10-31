"""Dataset wrapper that materializes fonts from remote Git repositories.

Examples:
    Synchronize a Git-based font corpus locally::

        repo_ds = FontRepo(
            root="data/fonts",
            url="https://example.com/fonts.git",
            ref="main",
            patterns=("**/*.ttf",),
            download=True,
        )

Requirements:
    The system must have ``git`` available in ``PATH`` and network access when
    ``download`` is set to ``True``.

"""

import shutil
import subprocess
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import SupportsIndex

from torchfont.datasets.folder import FontFolder, default_loader


class FontRepo(FontFolder):
    """Font dataset that synchronizes glyphs from a sparse Git checkout.

    See Also:
        FontFolder: Provides the glyph indexing logic reused here.

    """

    def __init__(
        self,
        root: Path | str,
        url: str,
        ref: str,
        *,
        patterns: Sequence[str],
        codepoint_filter: Sequence[SupportsIndex] | None = None,
        loader: Callable[
            [str, SupportsIndex | None, SupportsIndex],
            object,
        ] = default_loader,
        transform: Callable[[object], object] | None = None,
        download: bool = False,
    ) -> None:
        """Clone and index a Git repository of fonts.

        Args:
            root: Local directory that contains the Git working tree.
            url: Remote origin URL for the repository.
            ref: Git reference (branch, tag, or commit hash) to synchronize.
            patterns: Sparse-checkout patterns that describe which files to
                materialize. See the `git sparse-checkout` docs for syntax:
                <https://git-scm.com/docs/git-sparse-checkout>.
            codepoint_filter: Optional iterable that limits Unicode code points
                when indexing glyphs.
            loader: Callable that constructs a sample from a font/code point pair.
            transform: Optional callable applied to each sample from the loader.
            download: Whether to clone and check out the repository contents if
                the working tree is empty.

        Raises:
            RuntimeError: If Git is not available or the existing repository does
                not match the requested configuration.
            FileNotFoundError: If the repository does not exist locally and
                ``download`` is ``False``.

        Examples:
            Skip cloning when the working tree already matches the desired state::

                ds = FontRepo(
                    root="data/fonts",
                    url="https://github.com/google/fonts",
                    ref="main",
                    patterns=("ofl/*/*.ttf",),
                    download=False,
                )

        """
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
            loader=loader,
            transform=transform,
        )
