"""TorchFont: A PyTorch-based library for learning and processing vector fonts.

Overview:
    TorchFont bundles dataset utilities, tensor pens, and preprocessing transforms
    that streamline glyph-focused machine learning workflows.

Features:
    - Google Fonts integration via sparse Git checkouts.
    - Tensor-based glyph rendering with `fontTools` pens.
    - Transform primitives that handle batching and truncation.

Examples:
    Build a dataset sourced from Google Fonts::

        from torchfont.datasets import GoogleFonts
        ds = GoogleFonts(root="data/google_fonts", ref="main", download=True)

Further Reading:
    Consult the project README for installation guidance and advanced usage
    patterns.

"""
