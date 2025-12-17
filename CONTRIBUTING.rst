Contributing to TorchFont
=========================

Thank you for taking the time to improve TorchFont! The guidelines below keep
the project healthy and make it easier for maintainers to review changes.

Project Setup
-------------

TorchFont uses `uv <https://docs.astral.sh/uv/>`_ to manage virtual environments
and dependency locks.

.. code-block:: bash

   uv sync --all-groups

This installs the runtime package, development tooling (linters, tests), and the
documentation toolchain in a single isolated environment. Activate the shell
with ``uv run`` or prefix commands as shown later in this document.

Coding Standards
----------------

* The minimum supported Python version is 3.10. Avoid syntax that would break on
  that interpreter.
* Keep modules typed. ``pyproject.toml`` ships ``py.typed`` metadata, so mypy
  warnings matter.
* Public APIs live under ``torchfont.datasets`` and ``torchfont.transforms``.
  When adding modules, update ``docs/source/api`` so that Sphinx picks them up.

Linting & Type Checking
-----------------------

GitHub Actions runs linting and type-checking automatically after you open a
pull request. Keep an eye on the workflow status and address any failures that
appear. To reproduce issues locally, run:

.. code-block:: bash

   uv run ruff format --diff .
   uv run ruff check .
   uv run mypy python/torchfont

Testing
-------

By default, ``pytest`` skips slow and network-dependent tests to speed up local
development. Tests are organized by module in the ``tests/`` directory and use
pytest markers to categorize requirements:

.. code-block:: bash

   # Run only fast, offline tests (default)
   uv run pytest

   # Run all tests including slow/network tests
   uv run pytest --runslow --runnetwork

   # Run only network tests
   uv run pytest --runnetwork

   # Run only slow tests
   uv run pytest --runslow

The repository contains small integration samples inside ``examples/``. Please
exercise or extend them if your change alters their behavior.

Documentation
-------------

Every significant feature should include user-facing documentation:

1. Update ``docs/source`` with narrative text or API references.
2. Build the docs locally to ensure nothing regresses:

   .. code-block:: bash

      uv run sphinx-build -b html docs/source docs/build

3. If you touched any ``.rst`` files, regenerate message catalogs and refresh
   translations:

   .. code-block:: bash

      uv run sphinx-build -b gettext docs/source docs/locale/gettext
      uv run sphinx-intl update -p docs/locale/gettext -l ja

4. Translate the new strings inside ``docs/locale/ja/LC_MESSAGES``. The
   Japanese docs should stay reasonably idiomatic—feel free to adapt phrasing
   instead of providing literal translations.

Git Workflow
------------

* Create topic branches off ``main``.
* Write descriptive commit messages. Mention the relevant issue when applicable.
* Keep pull requests focused. Separate unrelated refactors or formatting changes
  into their own PRs.
* Ensure CI (lint, type-check, tests, docs) passes before requesting review.

Need Help?
----------

Open a GitHub Discussion or issue if anything here is unclear. The more context
you provide (logs, screenshots, sample fonts), the faster reviewers can help.
