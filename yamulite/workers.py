"""Qt-friendly background task runner."""
from __future__ import annotations

import traceback
from typing import Any, Callable, Optional

from PyQt6.QtCore import QObject, QRunnable, QThreadPool, pyqtSignal


class _Signals(QObject):
    result = pyqtSignal(object)
    error = pyqtSignal(str)
    finished = pyqtSignal()


class Task(QRunnable):
    def __init__(self, fn: Callable[..., Any], *args, **kwargs):
        super().__init__()
        # Prevent Qt from deleting the C++ runnable after run(); we manage
        # lifetime ourselves via `_live_tasks` so the _Signals QObject
        # survives long enough to deliver queued cross-thread signals.
        self.setAutoDelete(False)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = _Signals()

    def run(self) -> None:
        try:
            res = self.fn(*self.args, **self.kwargs)
        except Exception as e:
            traceback.print_exc()
            self.signals.error.emit(str(e))
        else:
            self.signals.result.emit(res)
        finally:
            self.signals.finished.emit()


_live_tasks: set = set()

# Separate pool for large numbers of low-priority network I/O (e.g. cover
# downloads) so they cannot starve interactive API calls like search.
_cover_pool: Optional[QThreadPool] = None


def cover_pool() -> QThreadPool:
    global _cover_pool
    if _cover_pool is None:
        _cover_pool = QThreadPool()
        _cover_pool.setMaxThreadCount(4)
    return _cover_pool


def run(fn, *args, on_result=None, on_error=None, on_finished=None,
        pool: Optional[QThreadPool] = None, **kwargs) -> Task:
    task = Task(fn, *args, **kwargs)
    if on_result:
        task.signals.result.connect(on_result)
    if on_error:
        task.signals.error.connect(on_error)
    if on_finished:
        task.signals.finished.connect(on_finished)
    # Keep the task (and its _Signals QObject) alive until its queued
    # `finished` signal has been delivered on the Qt thread.
    _live_tasks.add(task)
    task.signals.finished.connect(lambda t=task: _live_tasks.discard(t))
    (pool or QThreadPool.globalInstance()).start(task)
    return task
