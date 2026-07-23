"""Stage progress bars — the ``rich.progress`` analogue of R's ``progressr`` per-stage progress.

Each stage runner wraps its work in :func:`stage_progress`, a context manager that yields a
:class:`StageProgress`. The R model is mirrored exactly: a fixed number of *hard steps* advance
the bar (``progressr::progressor(steps = N)`` + ``progress()``), while long inner loops *pulse*
the description without advancing (R's ``progress(msg, amount = 0)``).

The whole display is gated by :attr:`~whep_digitize.general.options.RuntimeOptions.progress_enabled`
(R ``whep.progress.enabled``). When disabled, :func:`stage_progress` yields an inert
:class:`StageProgress` whose ``step`` / ``pulse`` are no-ops and which creates no ``rich`` live
display at all — so output and behavior are byte-identical to a run with no progress code.

Progress is a pure console side effect: it never touches the data frames, so it cannot affect
determinism or parity.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TextColumn,
    TimeElapsedColumn,
)

from whep_digitize.general.helpers.console import get_console


class StageProgress:
    """A single stage's progress handle (a thin wrapper over one ``rich`` task).

    Obtained from :func:`stage_progress`. ``step`` advances the bar by one hard step; ``pulse``
    only refreshes the description (for per-item inner loops). Both are no-ops when progress is
    disabled (``progress`` / ``task_id`` are ``None``), so callers need no ``if enabled`` guards.
    """

    __slots__ = ("_label", "_progress", "_task_id")

    def __init__(self, progress: Progress | None, task_id: TaskID | None, label: str) -> None:
        """Bind the handle to a ``rich`` progress + task (or to nothing, when disabled)."""
        self._progress = progress
        self._task_id = task_id
        self._label = label

    def step(self, message: str = "") -> None:
        """Advance the bar by one hard step, updating the description (R ``progress(msg)``)."""
        if self._progress is not None and self._task_id is not None:
            self._progress.update(self._task_id, advance=1, description=self._describe(message))

    def pulse(self, message: str = "") -> None:
        """Refresh the description without advancing (R ``progress(msg, amount = 0)``)."""
        if self._progress is not None and self._task_id is not None:
            self._progress.update(self._task_id, description=self._describe(message))

    def _describe(self, message: str) -> str:
        return f"{self._label}: {message}" if message else self._label


@contextmanager
def stage_progress(label: str, total: int, *, enabled: bool) -> Iterator[StageProgress]:
    """Yield a :class:`StageProgress` for a stage of ``total`` hard steps.

    Args:
        label: The stage label shown at the front of the bar (e.g. ``"import"``).
        total: The number of hard steps (``step`` calls) the stage will make.
        enabled: When ``False``, no ``rich`` display is created and the handle is inert.

    Yields:
        The :class:`StageProgress` handle for the stage.
    """
    if not enabled:
        yield StageProgress(None, None, label)
        return
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        console=get_console(),
        transient=True,
    ) as progress:
        task_id = progress.add_task(label, total=total)
        yield StageProgress(progress, task_id, label)
