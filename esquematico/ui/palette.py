"""Panel lateral con la biblioteca de símbolos clasificada por categorías."""

from __future__ import annotations

from typing import List, Optional

from PySide6.QtCore import QPointF, Qt, Signal
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import (
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..symbols.library import Symbol, categories


class SymbolPreview(QWidget):
    """Vista previa en miniatura de un símbolo."""

    def __init__(self, symbol: Symbol, size=52, parent=None) -> None:
        super().__init__(parent)
        self.symbol = symbol
        self.preview_size = size
        self.setFixedSize(size, size)

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        symbol = self.symbol
        max_s = max(symbol.width, symbol.height, 1)
        scale = (self.preview_size - 14) / max_s
        ox = self.width() / 2.0
        oy = self.height() / 2.0

        painter.setPen(QColor("#1a237e"))
        for prim in symbol.primitives:
            kind = prim.kind
            args = prim.args
            if kind == "line":
                painter.drawLine(
                    ox + args[0] * scale, oy + args[1] * scale,
                    ox + args[2] * scale, oy + args[3] * scale)
            elif kind == "circle":
                cx0 = ox + args[0] * scale
                cy0 = oy + args[1] * scale
                rad = args[2] * scale
                painter.setBrush(QColor("#1a237e") if prim.style.get("filled")
                                 else Qt.BrushStyle.NoBrush)
                painter.drawEllipse(cx0 - rad, cy0 - rad, 2 * rad, 2 * rad)
                painter.setBrush(Qt.BrushStyle.NoBrush)
            elif kind == "rect":
                painter.drawRect(
                    ox + args[0] * scale, oy + args[1] * scale,
                    args[2] * scale, args[3] * scale)
            elif kind == "text":
                painter.drawText(
                    ox + args[0] * scale, oy + args[1] * scale,
                    str(prim.style.get("text", "")))
            elif kind == "pin":
                painter.setBrush(QColor("#2f80ed"))
                painter.drawEllipse(QPointF(ox + args[0] * scale,
                                            oy + args[1] * scale), 3, 3)
                painter.setBrush(Qt.BrushStyle.NoBrush)


class SymbolPalette(QWidget):
    """Paleta lateral para seleccionar símbolos."""

    symbol_activated = Signal(object)  # Symbol

    def __init__(self, library: List[Symbol], parent=None) -> None:
        super().__init__(parent)
        self.library = library

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        title = QLabel("Biblioteca de símbolos")
        title.setObjectName("panelTitle")
        layout.addWidget(title)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Buscar símbolo...")
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self._apply_filter)
        layout.addWidget(self.search)

        self.list = QListWidget()
        self.list.setObjectName("symbolList")
        self.list.setSpacing(2)
        self.list.itemClicked.connect(self._on_clicked)
        layout.addWidget(self.list, 1)

        self._populate(None)

    def _populate(self, text: Optional[str]) -> None:
        self.list.clear()
        text = (text or "").strip().lower()
        for cat in categories(self.library):
            members = [s for s in self.library
                       if s.category == cat and
                       (not text or text in s.name.lower() or text in s.id.lower())]
            if not members:
                continue
            header = QListWidgetItem(cat)
            header.setFlags(Qt.ItemFlag.NoItemFlags)
            font = header.font()
            font.setBold(True)
            header.setFont(font)
            header.setForeground(QColor("#1565c0"))
            self.list.addItem(header)
            for s in members:
                item = QListWidgetItem(s.name)
                item.setData(Qt.ItemDataRole.UserRole, s)
                self.list.addItem(item)
                row = self.list.row(item)
                self.list.setItemWidget(item, SymbolPreview(s))
                item.setSizeHint(SymbolPreview(s).sizeHint())

    def _apply_filter(self, text: str) -> None:
        self._populate(text)

    def _on_clicked(self, item: QListWidgetItem) -> None:
        symbol = item.data(Qt.ItemDataRole.UserRole)
        if symbol is not None:
            self.symbol_activated.emit(symbol)
