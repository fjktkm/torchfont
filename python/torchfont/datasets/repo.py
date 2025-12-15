"""Dataset wrapper that materializes fonts from remote Git repositories.

Notes:
    Synchronization relies on ``pygit2``/``libgit2`` bindings and does not
    require the ``git`` CLI. Network access is still necessary when ``download``
    is ``True`` to refresh the on-disk shallow clone.

Examples:
    Synchronize a Git-based font corpus locally::

        repo_ds = FontRepo(
            root="data/fonts",
            url="https://example.com/fonts.git",
            ref="main",
            patterns=("**/*.ttf",),
            download=True,
        )

"""

from collections.abc import Callable, Sequence
from pathlib import Path
from typing import SupportsIndex

import pygit2

from torchfont.datasets.folder import FontFolder


class FontRepo(FontFolder):
    """Font dataset that synchronizes glyphs from a shallow Git clone.

    The clone fetches the requested reference at depth one, while
    :paramref:`patterns` restricts which fonts are indexed from the working
    tree.

    See Also:
        torchfont.datasets.folder.FontFolder: Provides the glyph indexing logic
        reused by this dataset.

    """

    def __init__(
        self,
        root: Path | str,
        url: str,
        ref: str,
        *,
        patterns: Sequence[str],
        codepoint_filter: Sequence[SupportsIndex] | None = None,
        transform: Callable[[object], object] | None = None,
        download: bool = False,
    ) -> None:
        """Clone and index a Git repository of fonts.

        Args:
            root (Path | str): Local directory that contains the Git working tree.
            url (str): Remote origin URL for the repository.
            ref (str): Git reference (branch, tag, or commit hash) to synchronize.
            patterns (Sequence[str]): Glob-style patterns applied when walking
                the working tree to select which font files to index.
            codepoint_filter (Sequence[SupportsIndex] | None): Optional iterable
                that limits Unicode code points when indexing glyphs.
            transform (Callable[[object], object] | None): Optional callable
                applied to each sample from the backend.
            download (bool): Whether to clone and check out the repository
                contents when the working tree is empty or stale.

        Raises:
            ValueError: If the existing repository does not match the requested
                configuration or syncing fails.
            FileNotFoundError: If the repository does not exist locally and
                ``download`` is ``False``.

        Examples:
            Skip cloning when the working tree already matches the desired
            state::

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
        self.patterns = tuple(patterns)

        git_dir = self.root / ".git"
        created = not git_dir.exists()

        if created:
            repo = pygit2.init_repository(str(self.root), origin_url=self.url)
        else:
            repo = pygit2.Repository(str(self.root))

        if created or download:
            repo.remotes["origin"].fetch([self.ref], depth=1)
            fetch_head = repo.lookup_reference("FETCH_HEAD")
            repo.checkout(fetch_head, strategy=pygit2.GIT_CHECKOUT_FORCE)  # type: ignore[attr-defined]

        commit = repo.head.peel()
        self.commit_hash = str(commit.id)

        super().__init__(
            root=self.root,
            codepoint_filter=codepoint_filter,
            patterns=self.patterns,
            transform=transform,
        )
