Contributing to TorchFont
=========================

Thank you for taking the time to improve TorchFont! The guidelines below keep
the project healthy and make it easier for maintainers to review changes.

Project Setup
-------------

TorchFont uses `uv <https://docs.astral.sh/uv/>`_ to manage virtual environments
and dependency locks.

.. code-block:: bash

   uv sync

This installs the runtime package and development tooling (linters, tests) in a
single isolated environment. Activate the shell with ``uv run`` or prefix
commands as shown later in this document.

Coding Standards
----------------

* The minimum supported Python version is 3.10. Avoid syntax that would break on
  that interpreter.
* Keep modules typed. ``pyproject.toml`` ships ``py.typed`` metadata, so ty
  warnings matter.
* Public APIs live under ``torchfont.datasets`` and ``torchfont.transforms``.

Linting & Type Checking
-----------------------

GitHub Actions runs linting and type-checking automatically after you open a
pull request. Keep an eye on the workflow status and address any failures that
appear. To reproduce issues locally, run:

.. code-block:: bash

   uv run ruff format --diff
   uv run ruff check
   uv run ty check

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

Git Workflow
------------

* Create topic branches off ``main``.
* Write descriptive commit messages. Mention the relevant issue when applicable.
* Keep pull requests focused. Separate unrelated refactors or formatting changes
  into their own PRs.
* Ensure CI (lint, type-check, tests) passes before requesting review.

Need Help?
----------

Open a GitHub Discussion or issue if anything here is unclear. The more context
you provide (logs, screenshots, sample fonts), the faster reviewers can help.
