Getting Started
===============

TorchFont ships a small but opinionated toolbox for working with vector fonts in
PyTorch. This page walks you through installation, validates the environment,
and provides a short end-to-end example that loads glyphs, applies transforms,
and feeds them into a dataloader.

Prerequisites
-------------

* Python 3.10 or newer
* PyTorch 2.3 or newer

Installation
------------

The recommended path is to manage dependencies with `uv <https://docs.astral.sh/uv/>`_.

.. code-block:: bash

   uv add torchfont

If you prefer pip, run:

.. code-block:: bash

   pip install torchfont

Confirm the installation by importing the package and printing the version number:

.. code-block:: python

   import torchfont
   print(torchfont.__version__)

Downloading Fonts
-----------------

TorchFont does not bundle any font assets. For a lightweight sandbox, clone a
subset of Google Fonts into ``data/google/fonts`` with the provided dataset helper:

.. code-block:: python

   from torchfont.datasets import GoogleFonts

   dataset = GoogleFonts(
       root="data/google/fonts",
       ref="main",
       download=True,  # performs the initial shallow clone
   )

The dataset keeps the shallow clone up to date on subsequent runs. Point ``root`` to any writable cache directory.

Progress Display
~~~~~~~~~~~~~~~~

When downloading or updating repositories, TorchFont displays progress information using the ``rich`` library. You can control this behavior using environment variables:

* Set ``TERM=dumb`` to disable all progress bars and styling
* Set ``TTY_INTERACTIVE=0`` to disable progress bar animations
* In CI/CD environments, use ``TTY_COMPATIBLE=1`` and ``TTY_INTERACTIVE=0`` together

First Glyph Dataset
-------------------

The :class:`torchfont.datasets.FontFolder` dataset turns a directory of ``.otf`` or ``.ttf`` files into an indexable PyTorch-style dataset. Each item contains the pen command types and normalized coordinates emitted by the compiled Rust backend, plus style/content labels.

.. code-block:: python

   from torch.utils.data import DataLoader

   from torchfont.datasets import FontFolder
   from torchfont.transforms import Compose, LimitSequenceLength, Patchify

   transform = Compose(
       (
           LimitSequenceLength(max_len=256),
           Patchify(patch_size=32),
       )
   )

   dataset = FontFolder(
       root="~/fonts",  # scans recursively
       codepoint_filter=[ord("A"), ord("B"), ord("C")],
       transform=transform,
   )

   def collate_fn(batch):
       types, coords, styles, contents = [], [], [], []
       for (sample, (style, content)) in batch:
           t, c = sample
           types.append(t)
           coords.append(c)
           styles.append(style)
           contents.append(content)
       return types, coords, styles, contents

   loader = DataLoader(dataset, batch_size=32, shuffle=True, collate_fn=collate_fn)
   types, coords, style_labels, content_labels = next(iter(loader))

Working with Google Fonts
-------------------------

The :class:`torchfont.datasets.GoogleFonts` dataset mirrors the official repository via a shallow clone and applies glob patterns when indexing. It exposes the same sample structure as :class:`FontFolder`, so you can reuse the same transforms and dataloaders:

.. code-block:: python

   from torchfont.datasets import GoogleFonts

   google/fonts = GoogleFonts(
       root="data/google/fonts",
       ref="main",
       transform=transform,
       download=True,
       patterns=("ofl/*/*.ttf", "ofl/*/*.otf"),
   )

   sample, (style_label, content_label) = google_fonts[0]

Next Steps
----------

* Continue to the :doc:`/user_guide/index` for a deeper dive into the dataset,
  transform, and I/O utilities.
* Review :doc:`/contributor_guide/index` if you plan to submit fixes or new
  features.
