"""Stage 0 — general pipeline: constants, config, directories, and shared helpers.

Ports ``r/0-general_pipeline/``. This is the shared foundation every other stage imports:
constants (:mod:`~whep_digitize.general.constants`), the per-run
:class:`~whep_digitize.general.config.Config`, runtime
:class:`~whep_digitize.general.options.RuntimeOptions`, directory construction, and the
:mod:`~whep_digitize.general.helpers` package.
"""

from __future__ import annotations
