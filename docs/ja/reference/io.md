# IO API

## `torchfont.io.outline`

グリフコマンドの共通定数です。

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

コマンド種別数。現在値は `6`。

### `COORD_DIM: int`

座標次元数。現在値は `6`（`[cp1_x, cp1_y, cp2_x, cp2_y, x, y]`）。

---

## `torchfont.io.git`

`FontRepo` / `GoogleFonts` の内部で使われる Git 同期関数です。

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

`root` を Git 作業ディレクトリとして整備し、指定 `ref` のコミットハッシュを返します。

- `download=True`: リモート fetch + force checkout
- `download=False`: ローカルで `ref` を解決して force checkout

チェックアウトは、作業ツリーを `ref` に揃える force 戦略で実行されます。

返り値は `commit_hash`（文字列）です。

::: info
通常は `FontRepo` / `GoogleFonts` から使えば十分です。`ensure_repo` を直接呼ぶのは、Git 同期処理を独自に制御したい場合だけで構いません。
:::
