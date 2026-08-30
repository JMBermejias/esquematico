"""Formulario de datos del proyecto.

Recoge los datos del proyecto (nombre, cliente, autor, fecha, escala, plano,
revisión, empresa) y los guarda en el diagrama para rellenar automáticamente
el cajetín del plano al exportarlo o visualizarlo.
"""

from __future__ import annotations

from datetime import date
from typing import Dict

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QVBoxLayout,
)

from ..core.model import DEFAULT_METADATA


class ProjectDialog(QDialog):
    """Cuadro de diálogo para introducir los datos del proyecto."""

    FIELDS = [
        ("proyecto", "Proyecto", True),
        ("cliente", "Cliente", False),
        ("empresa", "Empresa", False),
        ("autor", "Diseño / Autor", True),
        ("fecha", "Fecha", True),
        ("escala", "Escala", False),
        ("plano", "Plano Nº", False),
        ("revision", "Revisión", False),
    ]

    def __init__(self, parent=None, metadata: Dict[str, str] | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Datos del proyecto")
        self.setModal(True)
        self.resize(420, 360)

        meta = {**DEFAULT_METADATA, **(metadata or {})}
        self._edits = {}
        style = ("QLineEdit { background-color:#ffffff; border:1px solid #bcd9f6;"
                 "border-radius:5px; padding:4px; color:#1a237e; }")

        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        for key, label, _is_date in self.FIELDS:
            if key == "fecha":
                edit = QDateEdit()
                edit.setCalendarPopup(True)
                edit.setDisplayFormat("dd/MM/yyyy")
                fecha = meta.get("fecha", "")
                if fecha:
                    try:
                        d = date.fromisoformat(fecha[:10])
                        edit.setDate(d)
                    except ValueError:
                        pass
            else:
                edit = QLineEdit()
                edit.setText(meta.get(key, ""))
            edit.setStyleSheet(style)
            form.addRow(label + ":", edit)
            self._edits[key] = edit

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setStyleSheet("""
            QDialog { background-color: #eaf2fc; color: #1a237e;
                      font-family: 'Segoe UI'; font-size: 12px; }
            QLabel { color: #0d47a1; font-weight: bold; }
            QDateEdit { background-color: #ffffff; border: 1px solid #bcd9f6;
                        border-radius: 5px; padding: 4px; color: #1a237e; }
        """)

    def values(self) -> Dict[str, str]:
        meta: Dict[str, str] = {}
        for key, item in self._edits.items():
            if key == "fecha":
                meta[key] = item.date().toString("dd/MM/yyyy")
            else:
                meta[key] = item.text().strip()
        return meta
