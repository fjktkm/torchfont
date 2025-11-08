User Guide
==========

The sections below explain how the high-level modules fit together and provide
short recipes that you can adapt for your own training pipelines.

Datasets
--------

TorchFont exposes three dataset wrappers under :mod:`torchfont.datasets`.

``FontFolder``
   Scans a directory of ``.otf``/``.ttf`` files. Every available Unicode code
   point and variation instance becomes an item. Use the ``codepoint_filter``
   argument to limit the content and plug in a custom ``loader`` when you need
   extra preprocessing.

``GoogleFonts``
   Maintains a sparse checkout of the `google/fonts` repository. Pass ``patterns``
   to restrict which directories are materialized, and set ``download=True`` to
   ensure the checkout exists. The dataset inherits the same indexing and label
   structure as :class:`FontFolder`.

``FontRepo``
   Generalizes the sparse checkout logic to arbitrary Git repositories. Provide
   a ``url``, ``ref``, and optional ``patterns`` describing what to materialize.

Example – `FontRepo`
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from torchfont.datasets import FontRepo

   ibm_plex = FontRepo(
       root="data/font_repos",
       url="https://github.com/IBM/plex.git",
       ref="main",
       patterns=("fonts/Complete/OTF/*/*.otf",),
       download=True,
   )

   sample, (style_label, content_label) = ibm_plex[42]

Transforms
----------

Sequential transformations live under :mod:`torchfont.transforms`. Combine them
with :class:`torchfont.transforms.Compose` to keep preprocessing modules
declarative.

.. code-block:: python

   from torchfont.transforms import Compose, LimitSequenceLength, Patchify

   transform = Compose(
       (
           LimitSequenceLength(max_len=512),
           Patchify(patch_size=32),
       )
   )

   sample, labels = dataset[0]
   sample = transform(sample)

``LimitSequenceLength``
   Clips both the command-type tensor and the coordinate tensor to ``max_len``.

``Patchify``
   Zero-pads sequences to the next ``patch_size`` boundary, then reshapes them
   into contiguous patches—useful for transformer-style models.

I/O Utilities
-------------

The :mod:`torchfont.io` namespace contains helpers for converting raw outlines
to Tensors.

``torchfont.io.pens.TensorPen``
   Implements a FontTools-compatible pen that records every command as PyTorch
   tensors. The resulting tensors are what the datasets return, so you can reuse
   the pen when building custom loaders.

.. code-block:: python

   from fontTools.ttLib import TTFont
   from torchfont.io.pens import TensorPen

   font = TTFont("MyFont-Regular.otf")
   glyph_set = font.getGlyphSet()
   glyph = glyph_set["A"]
   pen = TensorPen(glyph_set)
   glyph.draw(pen)
   command_types, coords = pen.get_tensor()

Data Loading Tips
-----------------

* Glyph sequences vary in length. Always supply a ``collate_fn`` that pads or
  truncates samples before they are stacked into a batch.
* When working with ``GoogleFonts`` consider splitting the dataset into several
  :class:`torch.utils.data.Subset` objects and feeding them to Lightning's
  :class:`lightning.pytorch.utilities.combined_loader.CombinedLoader` (see
  ``examples/dataloader.py``) to parallelize IO.
* Cache-heavy datasets benefit from setting ``num_workers`` to at least the
  number of CPU cores available during preprocessing and inferencing.

Best Practices
--------------

* **Keep raw fonts immutable.** The caching performed by
  :func:`torchfont.datasets.folder.load_font` assumes files on disk are not
  modified while the process is running. Call ``load_font.cache_clear()`` if you
  need to invalidate the cache.
* **Separate style and content labels.** Every dataset returns both. Treat style
  (font instance) as one task and content (code point) as another so that your
  losses stay interpretable.
* **Document your Transform pipeline.** Store the pipeline configuration next to
  model checkpoints to keep glyph preprocessing reproducible.
