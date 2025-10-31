"""Composable transforms for preprocessing tensor glyph sequences.

Examples:
    ``Compose`` multiple operations to normalize glyph tensors::

        pipeline = Compose([LimitSequenceLength(256), Patchify(32)])

Background:
    The transforms aim to cover the common preprocessing steps for vectorized
    glyph data while still integrating cleanly with PyTorch ``Dataset``
    instances.

"""

from collections.abc import Callable, Sequence

import torch
from torch import Tensor


class Compose:
    """Apply a sequence of transform callables to each sample.

    See Also:
        LimitSequenceLength: Common building block for truncating sequences.

    """

    def __init__(self, transforms: Sequence[Callable[..., object]]) -> None:
        """Store the ordered transform pipeline.

        Args:
            transforms: Operations that accept and return matching sample types.

        Examples:
            Compose truncation with patching::

                Compose([LimitSequenceLength(256), Patchify(32)])

        """
        self.transforms = transforms

    def __call__(self, sample: object) -> object:
        """Apply every transform in order to the provided sample.

        Args:
            sample: Input sample passed to the first transform in the sequence.

        Returns:
            object: Resulting sample after all transformations are applied.

        Examples:
            Apply the composed operations to a glyph sample::

                sample = pipeline(sample)

        """
        for t in self.transforms:
            sample = t(sample)
        return sample


class LimitSequenceLength:
    """Trim glyph sequences to a fixed maximum length.

    See Also:
        Patchify: Converts sequences into fixed-size blocks after truncation.

    """

    def __init__(self, max_len: int) -> None:
        """Initialize the transform with the desired maximum length.

        Args:
            max_len: Maximum number of time steps to retain.

        Examples:
            Keep at most 512 steps per glyph::

                LimitSequenceLength(512)

        """
        self.max_len = max_len

    def __call__(self, sample: tuple[Tensor, Tensor]) -> tuple[Tensor, Tensor]:
        """Clip the sequence and coordinate tensors to the configured length.

        Args:
            sample: Tuple of ``(types, coords)`` tensors representing pen commands
                and control points.

        Returns:
            tuple[Tensor, Tensor]: Tuple with both tensors truncated to
            ``max_len`` elements.

        Warning:
            Extra elements beyond ``max_len`` are discarded without padding or
            aggregation.

        Examples:
            Clamp a sample to 128 steps::

                types, coords = LimitSequenceLength(128)((types, coords))

        """
        types, coords = sample

        types = types[: self.max_len]
        coords = coords[: self.max_len]

        return types, coords


class Patchify:
    """Pad glyph sequences and reshape them into equal-sized patches.

    See Also:
        LimitSequenceLength: Use together to enforce a strict maximum before
        patchification.

    """

    def __init__(self, patch_size: int) -> None:
        """Configure the patch length for reshaping sequences.

        Args:
            patch_size: Number of steps captured in each patch.

        Examples:
            Create 32-step patches for transformer models::

                Patchify(32)

        """
        self.patch_size = patch_size

    def __call__(self, sample: tuple[Tensor, Tensor]) -> tuple[Tensor, Tensor]:
        """Pad and reshape sequences into contiguous patches.

        Args:
            sample: Tuple of ``(types, coords)`` tensors representing pen commands
                and control points.

        Returns:
            tuple[Tensor, Tensor]: Tensors grouped into patches of ``patch_size``
            steps, including any zero padding required for alignment.

        Tips:
            Combine with :class:`LimitSequenceLength` to bound the number of
            generated patches.

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
