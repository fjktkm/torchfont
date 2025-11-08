"""Composable transforms for polishing tensor glyph sequences before training.

Notes:
    Each transform is intentionally small and deterministic, allowing you to mix
    and match them in :class:`torch.utils.data.Dataset` pipelines without losing
    track of where normalization occurs.

Examples:
    Normalize and patch glyph tensors in a single pipeline::

        pipeline = Compose([LimitSequenceLength(256), Patchify(32)])

"""

from collections.abc import Callable, Sequence

import torch
from torch import Tensor


class Compose:
    """Apply a curated list of transform callables to every sample.

    See Also:
        LimitSequenceLength: Useful when a hard cap is required before adding
        more expensive stages.

    """

    def __init__(self, transforms: Sequence[Callable[..., object]]) -> None:
        """Store the ordered transform pipeline.

        Args:
            transforms (Sequence[Callable[..., object]]): Operations that accept
                and return compatible sample types. Ordering matters, so place
                stateful or lossy transforms later in the list.

        Examples:
            Combine truncation with patching::

                Compose([LimitSequenceLength(256), Patchify(32)])

        """
        self.transforms = transforms

    def __call__(self, sample: object) -> object:
        """Apply every transform in order to the provided sample.

        Args:
            sample (object): Input passed to the first transform in the sequence.

        Returns:
            object: Resulting sample after all transformations are applied.

        Examples:
            Run the composed pipeline on a glyph sample::

                sample = pipeline(sample)

        """
        for t in self.transforms:
            sample = t(sample)
        return sample


class LimitSequenceLength:
    """Trim glyph sequences to a predictable maximum length.

    See Also:
        Patchify: Converts sequences into fixed-size blocks after truncation so
        transformer-style models see a uniform layout.

    """

    def __init__(self, max_len: int) -> None:
        """Initialize the transform with the desired maximum length.

        Args:
            max_len (int): Maximum number of time steps to keep. Any surplus
                command or coordinate pairs are discarded.

        Examples:
            Cap sequences at 512 steps::

                LimitSequenceLength(512)

        """
        self.max_len = max_len

    def __call__(self, sample: tuple[Tensor, Tensor]) -> tuple[Tensor, Tensor]:
        """Clip the sequence and coordinate tensors to the specified length.

        Args:
            sample (tuple[Tensor, Tensor]): Tuple of ``(types, coords)`` tensors
                representing pen commands and control points.

        Returns:
            tuple[Tensor, Tensor]: Tensors truncated to ``max_len`` elements.

        Warnings:
            Elements beyond ``max_len`` are removed rather than padded or
            aggregated, so downstream code should account for the shorter tail.

        Examples:
            Clamp a sample to 128 steps::

                types, coords = LimitSequenceLength(128)((types, coords))

        """
        types, coords = sample

        types = types[: self.max_len]
        coords = coords[: self.max_len]

        return types, coords


class Patchify:
    """Pad glyph sequences and reshape them into uniform, model-friendly patches.

    See Also:
        LimitSequenceLength: Apply beforehand when you need a strict ceiling on
        the number of emitted patches.

    """

    def __init__(self, patch_size: int) -> None:
        """Configure the patch length for reshaping sequences.

        Args:
            patch_size (int): Number of time steps captured in each patch. Choose
                values that align with the receptive field of your downstream
                model.

        Examples:
            Create 32-step patches for transformer models::

                Patchify(32)

        """
        self.patch_size = patch_size

    def __call__(self, sample: tuple[Tensor, Tensor]) -> tuple[Tensor, Tensor]:
        """Pad and reshape sequences into contiguous patches.

        Args:
            sample (tuple[Tensor, Tensor]): Tuple of ``(types, coords)``
                tensors representing pen commands and control points.

        Returns:
            tuple[Tensor, Tensor]: Tensors grouped into patches of
            ``patch_size`` steps. Trailing zeros are added only when needed for
            alignment.

        Tips:
            Pair with :class:`LimitSequenceLength` to bound the worst-case number
            of patches in a batch.

        Examples:
            Reshape a glyph sequence into patches of 64 steps::

                patch_types, patch_coords = Patchify(64)((types, coords))

        """
        types, coords = sample

        seq_len = types.size(0)
        pad = (-seq_len) % self.patch_size
        num_patches = (seq_len + pad) // self.patch_size

        pad_types = torch.cat([types, types.new_zeros(pad)], 0)
        pad_coords = torch.cat([coords, coords.new_zeros(pad, coords.size(1))], 0)

        patch_types = pad_types.view(num_patches, self.patch_size)
        patch_coords = pad_coords.view(num_patches, self.patch_size, coords.size(1))

        return patch_types, patch_coords
