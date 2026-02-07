# DataLoader Integration

TorchFont datasets subclass `torch.utils.data.Dataset`, so they fit standard
PyTorch training loops.

## Quick sanity check (`batch_size=1`)

```python
from torch.utils.data import DataLoader
from torchfont.datasets import FontFolder

dataset = FontFolder(root="~/fonts")
loader = DataLoader(dataset, batch_size=1, shuffle=True)

types, coords, style_idx, content_idx = next(iter(loader))
print(types.shape, coords.shape)  # (1, seq_len), (1, seq_len, 6)
print(style_idx.shape, content_idx.shape)  # (1,), (1,)
```

Use this only to check end-to-end wiring. For `batch_size > 1`, variable-length
glyph sequences usually require a custom `collate_fn`.

## Recommended `collate_fn` for training

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

`num_workers > 0` enables worker prefetching and multiprocessing context.
Keep those options unset when `num_workers=0`.

| Platform | Recommended `multiprocessing_context` |
| -------- | ------------------------------------- |
| Linux    | `"fork"`                              |
| macOS    | `"spawn"` or `"forkserver"`           |
| Windows  | `"spawn"`                             |

## Build a padding mask

`types == 0` identifies padding tokens (`pad`).

```python
padding_mask = types == 0
```

## Using `Patchify`

`Patchify` splits each sample into fixed-size patches, which simplifies batching
logic.

```python
from torchfont.transforms import Compose, LimitSequenceLength, Patchify

transform = Compose([
    LimitSequenceLength(max_len=512),
    Patchify(patch_size=32),
])
```

After this transform, `types.shape` becomes `(num_patches, 32)`. If you still
batch whole samples, `num_patches` can vary across samples, so `pad_sequence`
may still be required in `collate_fn`.
