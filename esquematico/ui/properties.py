"""Panel de propiedades del símbolo seleccionado."""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QColorDialog,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..core.model import SymbolInstance

COLORS = {
    "#2c3e50": "Azul oscuro",
    "#1565c0": "Azul",
    "#c62828": "Rojo",
    "#2e7d32": "Verde",
    "#6a1b9a": "Morado",
    "#ef6c00": "Naranja",
    "#000000": "Negro",
}


class PropertiesPanel(QWidget):
    """Muestra y edita las propiedades del símbolo seleccionado."""

    changed = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._inst: Optional[SymbolInstance] = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        title = QLabel("Propiedades")
        title.setObjectName("panelTitle")
        layout.addWidget(title)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.name_label = QLabel("—")
        self.name_label.setWordWrap(True)
        form.addRow("Símbolo:", self.name_label)

        self.label_edit = QLineEdit()
        self.label_edit.setPlaceholderText("Etiqueta / referencia")
        self.label_edit.editingFinished.connect(self._apply)
        form.addRow("Etiqueta:", self.label_edit)

        self.rotation = QDoubleSpinBox()
        self.rotation.setRange(0, 360)
        self.rotation.setDecimals(0)
        self.rotation.setSuffix("°")
        self.rotation.valueChanged.connect(self._apply)
        form.addRow("Rotación:", self.rotation)

        self.scale = QDoubleSpinBox()
        self.scale.setRange(0.2, 5.0)
        self.scale.setDecimals(2)
        self.scale.setSingleStep(0.1)
        self.scale.valueChanged.connect(self._apply)
        form.addRow("Escala:", self.scale)

        self.color_combo = QComboBox()
        for code, name in COLORS.items():
            self.color_combo.addItem(name, code)
        self.color_combo.currentIndexChanged.connect(self._apply)
        form.addRow("Color:", self.color_combo)

        self.color_btn = QPushButton("Personalizar color...")
        self.color_btn.clicked.connect(self._pick_color)
        form.addRow("", self.color_btn)

        layout.addLayout(form)
        layout.addStretch(1)

    def set_symbol(self, inst: Optional[SymbolInstance]) -> None:
        self._inst = inst
        self._loading = True
        try:
            if inst is None:
                self.name_label.setText("—")
                self.label_edit.clear()
                self.label_edit.setEnabled(False)
                self.rotation.setValue(0)
                self.rotation.setEnabled(False)
                self.scale.setValue(1)
                self.scale.setEnabled(False)
                self.color_combo.setEnabled(False)
                self.color_btn.setEnabled(False)
            else:
                self.name_label.setText(
                    getattr(inst, "_symbol_name", "Símbolo"))
                self.label_edit.setText(inst.label)
                self.label_edit.setEnabled(True)
                self.rotation.setValue(inst.rotation)
                self.rotation.setEnabled(True)
                self.scale.setValue(inst.scale)
                self.scale.setEnabled(True)
                idx = self.color_combo.findData(inst.color)
                if idx >= 0:
                    self.color_combo.setCurrentIndex(idx)
                self.color_combo.setEnabled(True)
                self.color_btn.setEnabled(True)
        finally:
            self._loading = False

    def _apply(self) -> None:
        if self._loading or self._inst is None:
            return
        self._inst.label = self.label_edit.text()
        self._inst.rotation = self.rotation.value()
        self._inst.scale = self.scale.value()
        self._inst.color = self.color_combo.currentData() or self._inst.color
        self.changed.emit()

    def _pick_color(self) -> None:
        if self._inst is None:
            return
        from PySide6.QtGui import QColor
        color = QColorDialog.getColor(QColor(self._inst.color), self,
                                      "Elegir color")
        if color.isValid():
            hexcode = color.name()
            self._inst.color = hexcode
            idx = self.color_combo.findData(hexcode)
            if idx < 0:
                self.color_combo.addItem(hexcode, hexcode)
                self.color_combo.setCurrentIndex(self.color_combo.count() - 1)
            else:
                self.color_combo.setCurrentIndex(idx)
            self.changed.emit()
