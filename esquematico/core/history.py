"""Historial de deshacer/rehacer basado en instantáneas del documento.

Cada operación de edición registra una instantánea del estado del diagrama
antes de la operación. Al deshacer/rehacer se restaura el estado guardado.
Las operaciones continuas (arrastrar un símbolo, girar un valor del panel)
se agrupan en un único paso de historial mediante checkpoint()/commit().
"""

from __future__ import annotations

import copy
from typing import Optional

from PySide6.QtCore import QObject, Signal


class History(QObject):
    """Gestor de deshacer/rehacer sobre un Diagram."""

    changed = Signal()

    def __init__(self, diagram=None, limit: int = 150) -> None:
        super().__init__()
        self.diagram = diagram
        self.limit = limit
        self.undo_stack = []
        self.redo_stack = []
        self._pending = None
        self._pending_valid = False

    # ------------------------------------------------------------------
    # Gestión del documento
    # ------------------------------------------------------------------
    def attach(self, diagram) -> None:
        self.diagram = diagram
        self.reset()

    def reset(self) -> None:
        self.undo_stack = []
        self.redo_stack = []
        self._pending = None
        self._pending_valid = False
        self.changed.emit()

    def _snapshot(self):
        return copy.deepcopy(self.diagram.to_dict())

    def _restore(self, data) -> None:
        self.diagram.load_dict(data)

    # ------------------------------------------------------------------
    # Registro de operaciones
    # ------------------------------------------------------------------
    def checkpoint(self) -> None:
        """Guarda el estado previo de la operación en curso (una sola vez)."""
        if self.diagram is None:
            return
        if not self._pending_valid:
            self._pending = self._snapshot()
            self._pending_valid = True

    def commit(self) -> None:
        """Confirma la operación: si hubo cambios, crea un paso de deshacer."""
        if not self._pending_valid:
            return
        before = self._pending
        after = self._snapshot()
        self._pending = None
        self._pending_valid = False
        if after == before:
            return
        self.undo_stack.append(before)
        self.redo_stack.clear()
        if len(self.undo_stack) > self.limit:
            self.undo_stack.pop(0)
        self.changed.emit()

    # ------------------------------------------------------------------
    # Deshacer / rehacer
    # ------------------------------------------------------------------
    def undo(self) -> bool:
        self._pending = None
        self._pending_valid = False
        if not self.undo_stack:
            return False
        current = self._snapshot()
        previous = self.undo_stack.pop()
        self.redo_stack.append(current)
        self._restore(previous)
        self.changed.emit()
        return True

    def redo(self) -> bool:
        if not self.redo_stack:
            return False
        current = self._snapshot()
        nxt = self.redo_stack.pop()
        self.undo_stack.append(current)
        self._restore(nxt)
        self.changed.emit()
        return True

    def can_undo(self) -> bool:
        return bool(self.undo_stack)

    def can_redo(self) -> bool:
        return bool(self.redo_stack)
