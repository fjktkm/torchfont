# Glyph Data Format

TorchFont datasets return each glyph sample as:

```python
types, coords, style_idx, content_idx = dataset[i]
```

| Element       | Type                | Shape          | Meaning              |
| ------------- | ------------------- | -------------- | -------------------- |
| `types`       | `torch.LongTensor`  | `(seq_len,)`   | Pen command sequence |
| `coords`      | `torch.FloatTensor` | `(seq_len, 6)` | Coordinate sequence  |
| `style_idx`   | `int`               | scalar         | Style class ID       |
| `content_idx` | `int`               | scalar         | Content class ID     |

## `types`

```python
from torchfont.io.outline import TYPE_TO_IDX

print(TYPE_TO_IDX)
# {
#   "pad": 0,
#   "moveTo": 1,
#   "lineTo": 2,
#   "curveTo": 3,
#   "closePath": 4,
#   "eos": 5,
# }
```

- `eos` marks end of sequence
- `pad` is mainly introduced by `pad_sequence` or `Patchify`

## `coords`

Each step uses a 6D vector:

```text
[cp1_x, cp1_y, cp2_x, cp2_y, x, y]
```

- `moveTo` / `lineTo`: control points are zero; endpoint `(x, y)` is used
- `curveTo`: two control points `(cp1, cp2)` and the endpoint `(x, y)` are used
- `closePath` / `eos` / `pad`: zeros

::: info
Coordinates are normalized by the font `units_per_em`.
:::

## Quadratic Bezier handling

Quadratic curves (common in TrueType) are converted to cubic form internally, so
`coords.shape[-1]` is always `6`.

## Style and content labels

### `style_idx`

- static fonts: usually `Family + Subfamily` (e.g. `Lato Regular`)
- variable fonts: one class per named instance when available
- variable fonts with empty instance names: `Family` only
- variable fonts without named instances: fallback to `Family + Subfamily` (or
  `Family`)

```python
print(dataset.style_classes[:5])
print(dataset.style_class_to_idx)
```

::: warning
`style_classes` can include duplicate names. In that case,
`style_class_to_idx` keeps only the last occurrence of each name.
When duplicate-safe filtering is required, enumerate `style_classes` directly.
:::

### `content_idx`

- one class per Unicode character

```python
print(dataset.content_classes[:5])
print(dataset.content_class_to_idx)
```

## `targets`

```python
t = dataset.targets  # shape: (N, 2), dtype: torch.long

style_all = t[:, 0]    # column 0: style_idx
content_all = t[:, 1]  # column 1: content_idx
```

## Shapes after transforms

With `Patchify`:

- before: `types=(seq_len,)`, `coords=(seq_len, 6)`
- after: `types=(num_patches, patch_size)`,
  `coords=(num_patches, patch_size, 6)`

`style_idx` and `content_idx` stay unchanged.
