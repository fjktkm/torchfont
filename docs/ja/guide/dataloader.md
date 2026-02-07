# DataLoader との統合

<!-- markdownlint-disable MD013 -->

TorchFont の Dataset は `torch.utils.data.Dataset` を継承しているため、通常の PyTorch ワークフローで使えます。

## まずは最小確認（`batch_size=1`）

```python
from torch.utils.data import DataLoader
from torchfont.datasets import FontFolder

dataset = FontFolder(root="~/fonts")
loader = DataLoader(dataset, batch_size=1, shuffle=True)

types, coords, style_idx, content_idx = next(iter(loader))
print(types.shape, coords.shape)  # (1, seq_len), (1, seq_len, 6)
print(style_idx.shape, content_idx.shape)  # (1,), (1,)
```

この例は動作確認用です。`batch_size > 1` では可変長シーケンスを扱うため、通常は専用 `collate_fn` が必要です。

## 学習向けの `collate_fn`

```python
from collections.abc import Sequence
import sys

import torch
from torch import Tensor
from torch.nn.utils.rnn import pad_sequence
from torch.utils.data import DataLoader

from torchfont.datasets import GoogleFonts


def collate_fn(
    batch: Sequence[tuple[Tensor, Tensor, int, int]],
) -> tuple[Tensor, Tensor, Tensor, Tensor]:
    types_list = [t for t, _, _, _ in batch]
    coords_list = [c for _, c, _, _ in batch]
    style_list = [s for _, _, s, _ in batch]
    content_list = [c for _, _, _, c in batch]

    types = pad_sequence(types_list, batch_first=True, padding_value=0)
    coords = pad_sequence(coords_list, batch_first=True, padding_value=0.0)

    style_idx = torch.as_tensor(style_list, dtype=torch.long)
    content_idx = torch.as_tensor(content_list, dtype=torch.long)
    return types, coords, style_idx, content_idx


dataset = GoogleFonts(root="data/google/fonts", ref="main", download=True)
num_workers = 8
mp_context = "fork" if sys.platform.startswith("linux") else "spawn"

loader_kwargs = {
    "batch_size": 64,
    "shuffle": True,
    "num_workers": num_workers,
    "collate_fn": collate_fn,
}

if num_workers > 0:
    loader_kwargs["prefetch_factor"] = 2
    loader_kwargs["multiprocessing_context"] = mp_context

loader = DataLoader(dataset, **loader_kwargs)
```

`num_workers > 0` のときだけ、プリフェッチと multiprocessing の設定を有効にします。`num_workers=0` なら、これらの引数は指定しないでください。

|OS|推奨 `multiprocessing_context`|
|---|---|
|Linux|`"fork"`|
|macOS|`"spawn"` または `"forkserver"`|
|Windows|`"spawn"`|

## パディングマスクを作る

`types` の `0` は `pad` なので、簡単にマスクが作れます。

```python
padding_mask = types == 0
```

## `Patchify` を使う場合

`Patchify` で固定長パッチへ分割しておくと、バッチ時の扱いが単純になります。

```python
from torchfont.transforms import Compose, LimitSequenceLength, Patchify

transform = Compose([
    LimitSequenceLength(max_len=512),
    Patchify(patch_size=32),
])
```

この場合、`types.shape` は `(num_patches, 32)` になります。サンプルごとに `num_patches` が異なる可能性は残るため、サンプル単位でバッチ化するなら `collate_fn` 側で `pad_sequence` が必要になることがあります。
