# IO API

## `torchfont.io.outline`

Shared constants for glyph command encoding.

```python
from torchfont.io.outline import TYPE_TO_IDX, TYPE_DIM, COORD_DIM
```

### `TYPE_TO_IDX: dict[str, int]`

```python
{
    "pad": 0,
    "moveTo": 1,
    "lineTo": 2,
    "curveTo": 3,
    "closePath": 4,
    "eos": 5,
}
```

### `TYPE_DIM: int`

Number of command types. Current value: `6`.

### `COORD_DIM: int`

Coordinate dimension. Current value: `6` (`[cp1_x, cp1_y, cp2_x, cp2_y, x, y]`).

---

## `torchfont.io.git`

Internal Git synchronization utility used by `FontRepo` and `GoogleFonts`.

```python
from torchfont.io.git import ensure_repo
```

### `ensure_repo(...) -> str`

```python
def ensure_repo(
    root: Path | str,
    url: str,
    ref: str,
    *,
    download: bool,
) -> str
```

Prepares/synchronizes `root` as a Git working tree and returns the checked-out
commit hash.

- `download=True`: fetch + force-checkout from remote
- `download=False`: local ref resolution + force-checkout

Checkout uses a force strategy to align the working tree with `ref`.

Return value: `commit_hash` as `str`.

::: info
Most users should call `FontRepo` / `GoogleFonts` rather than using
`ensure_repo` directly.
:::
