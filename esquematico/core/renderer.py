"""Renderizado del diagrama sobre un QPainter.

Se encarga de dibujar el fondo, la cuadrícula, los cables y cada símbolo
a partir de sus primitivas, aplicando rotación, escala y color.
"""

from __future__ import annotations

import math
from typing import List, Optional

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (
    QColor,
    QFont,
    QPainter,
    QPainterPath,
    QPen,
    QPolygonF,
)

from ..core.model import Diagram, SymbolInstance, Wire
from ..symbols.library import Symbol


def _transform_point(x: float, y: float, cx: float, cy: float,
                     rotation: float) -> QPointF:
    """Aplica rotación alrededor de (cx, cy)."""
    if rotation == 0:
        return QPointF(x, y)
    rad = math.radians(rotation)
    cos, sin = math.cos(rad), math.sin(rad)
    dx, dy = x - cx, y - cy
    return QPointF(cx + dx * cos - dy * sin, cy + dx * sin + dy * cos)


class DiagramRenderer:
    """Dibuja un Diagram en el QPainter proporcionado."""

    def __init__(self, painter: QPainter, diagram: Diagram,
                 symbol_lookup: dict) -> None:
        self.painter = painter
        self.diagram = diagram
        self.symbol_lookup = symbol_lookup

    def draw_background(self) -> None:
        p = self.painter
        rect = QRectF(0, 0, self.diagram.width, self.diagram.height)
        p.fillRect(rect, QColor(self.diagram.background))

    def draw_grid(self, grid_on: bool = True) -> None:
        """Dibuja la cuadrícula como puntos grises visibles (referencias)
        para facilitar la alineación de los elementos del plano."""
        if not grid_on:
            return
        p = self.painter
        g = self.diagram.grid_size
        r = 3.0
        path = QPainterPath()
        y = 0.0
        while y <= self.diagram.height:
            x = 0.0
            while x <= self.diagram.width:
                path.addEllipse(QPointF(x, y), r, r)
                x += g
            y += g
        p.save()
        pen = QPen(QColor("#6d6d6d"), 1)
        p.setPen(pen)
        p.setBrush(QColor("#6d6d6d"))
        p.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        p.drawPath(path)
        p.restore()

    def draw_wires(self, wires: List[Wire]) -> None:
        p = self.painter
        for w in wires:
            pen = QPen(QColor(w.color), w.width)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            p.setPen(pen)
            p.drawLine(QPointF(w.x1, w.y1), QPointF(w.x2, w.y2))
            if w.label:
                p.setPen(QPen(QColor("#34495e"), 1))
                f = QFont("Segoe UI", 9)
                p.setFont(f)
                p.drawText(
                    QRectF((w.x1 + w.x2) / 2 - 40, (w.y1 + w.y2) / 2 - 10,
                           80, 20),
                    Qt.AlignmentFlag.AlignCenter, w.label,
                )

    def draw_symbol(self, inst: SymbolInstance, symbol: Symbol,
                    selected: bool = False, draw_pins: bool = True) -> None:
        p = self.painter
        cx, cy = inst.x, inst.y
        rot = inst.rotation

        color = QColor(inst.color)
        pen = QPen(color, 2.0)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)

        scale = inst.scale
        half_w = symbol.width / 2.0 * scale
        half_h = symbol.height / 2.0 * scale

        for prim in symbol.primitives:
            kind = prim.kind
            args = prim.args
            if kind == "line":
                x1 = _transform_point(cx + args[0] * scale, cy + args[1] * scale,
                                      cx, cy, rot)
                x2 = _transform_point(cx + args[2] * scale, cy + args[3] * scale,
                                      cx, cy, rot)
                pen.setColor(QColor(prim.style.get("color", inst.color)))
                pen.setWidthF(float(prim.style.get("width", 2.0)))
                p.setPen(pen)
                p.drawLine(x1, x2)

            elif kind == "circle":
                cx0 = _transform_point(cx + args[0] * scale, cy + args[1] * scale,
                                       cx, cy, rot)
                r = args[2] * scale
                pen.setColor(QColor(prim.style.get("color", inst.color)))
                pen.setWidthF(float(prim.style.get("width", 2.0)))
                p.setPen(pen)
                if prim.style.get("filled"):
                    p.setBrush(color)
                else:
                    p.setBrush(Qt.BrushStyle.NoBrush)
                p.drawEllipse(QRectF(cx0.x() - r, cx0.y() - r, 2 * r, 2 * r))

            elif kind == "rect":
                x1 = cx + args[0] * scale
                y1 = cy + args[1] * scale
                w = args[2] * scale
                h = args[3] * scale
                pen.setColor(QColor(prim.style.get("color", inst.color)))
                pen.setWidthF(float(prim.style.get("width", 2.0)))
                p.setPen(pen)
                p.setBrush(Qt.BrushStyle.NoBrush)

                def _draw_rect() -> None:
                    rect = QRectF(x1, y1, w, h)
                    if prim.style.get("rounded"):
                        p.drawRoundedRect(rect, 8, 8)
                    else:
                        p.drawRect(rect)

                if rot != 0:
                    p.save()
                    p.translate(cx, cy)
                    p.rotate(rot)
                    p.translate(-cx, -cy)
                    _draw_rect()
                    p.restore()
                else:
                    _draw_rect()

            elif kind == "arc":
                pass

            elif kind == "text":
                x = cx + args[0] * scale
                y = cy + args[1] * scale
                text = str(prim.style.get("text", args[2] if len(args) > 2 else ""))
                f = QFont("Segoe UI", int(prim.style.get("size", 14)))
                p.setFont(f)
                pen.setColor(QColor(prim.style.get("color", inst.color)))
                p.setPen(pen)
                if prim.style.get("bold"):
                    f.setBold(True)
                    p.setFont(f)
                p.drawText(QPointF(x, y), text)

        # Etiqueta del usuario
        if inst.label:
            f = QFont("Segoe UI", 10)
            f.setBold(True)
            p.setFont(f)
            p.setPen(QPen(QColor("#1565c0"), 1))
            p.drawText(
                QPointF(cx - 60, cy + half_h + 16),
                inst.label,
            )

        # Pines (puntos de conexión)
        if draw_pins:
            self.draw_pins(inst, symbol)
            self.draw_rotation_marker(inst, cx, cy, half_w, half_h)

        # Selección
        if selected:
            self.draw_selection(inst, cx, cy, half_w, half_h)

    def draw_pins(self, inst: SymbolInstance, symbol: Symbol) -> None:
        p = self.painter
        pin_pen = QPen(QColor("#2f80ed"), 1)
        p.setPen(pin_pen)
        p.setBrush(QColor("#2f80ed"))
        for prim in symbol.primitives:
            if prim.kind == "pin":
                px = _transform_point(inst.x + prim.args[0] * inst.scale,
                                      inst.y + prim.args[1] * inst.scale,
                                      inst.x, inst.y, inst.rotation)
                p.drawEllipse(px, 3)

    def draw_rotation_marker(self, inst: SymbolInstance, cx, cy,
                             half_w, half_h) -> None:
        p = self.painter
        # Marcador de orientación
        marker = _transform_point(cx + half_w + 4, cy - half_h - 4, cx, cy,
                                  inst.rotation)
        p.setPen(QPen(QColor("#90a4ae"), 2))
        p.drawLine(marker, _transform_point(cx + half_w + 4, cy - half_h - 4,
                                            cx, cy, 0))

    def draw_selection(self, inst: SymbolInstance, cx, cy, half_w, half_h) -> None:
        p = self.painter
        pen = QPen(QColor("#2196f3"), 1.5)
        pen.setStyle(Qt.PenStyle.DashLine)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRect(QRectF(cx - half_w - 6, cy - half_h - 6,
                          half_w * 2 + 12, half_h * 2 + 12))

    def draw(self, show_grid: bool = True, selected: Optional[str] = None,
             draw_pins: bool = True) -> None:
        self.draw_background()
        self.draw_grid(show_grid)
        self.draw_wires(self.diagram.wires)
        for inst in self.diagram.symbols:
            try:
                symbol = self.symbol_lookup[inst.symbol_id]
            except KeyError:
                continue
            self.draw_symbol(inst, symbol,
                             selected=(selected == id(inst)),
                             draw_pins=draw_pins)
        self.draw_sheet()

    # ------------------------------------------------------------------
    # Plano: marco de hoja y cajetín de datos del proyecto
    # ------------------------------------------------------------------
    SHEET_MARGIN = 25.0
    BLOCK_W = 360.0
    BLOCK_H = 132.0

    def draw_sheet(self) -> None:
        """Dibuja el marco de la hoja (borde del plano)."""
        p = self.painter
        w, h = self.diagram.width, self.diagram.height
        m = self.SHEET_MARGIN
        p.save()
        pen = QPen(QColor("#1a237e"), 3)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRect(QRectF(m, m, w - 2 * m, h - 2 * m))
        p.restore()

    def draw_title_block(self) -> None:
        """Dibuja el cajetín de datos del proyecto en la esquina inferior
        derecha del plano."""
        p = self.painter
        w, h = self.diagram.width, self.diagram.height
        m = self.SHEET_MARGIN
        bw, bh = self.BLOCK_W, self.BLOCK_H
        bx = w - m - bw
        by = h - m - bh
        meta = self.diagram.metadata

        p.save()
        # Marco exterior del cajetín
        pen = QPen(QColor("#1a237e"), 2)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRect(QRectF(bx, by, bw, bh))

        # Banda de cabecera
        header_h = 22
        p.fillRect(QRectF(bx, by, bw, header_h), QColor("#bcd9f6"))
        f = QFont("Segoe UI", 10)
        f.setBold(True)
        p.setFont(f)
        p.setPen(QPen(QColor("#0d47a1"), 1))
        p.drawText(QRectF(bx + 4, by + 2, bw - 8, header_h - 4),
                   Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                   "PLANO DE PROYECTO ELÉCTRICO")

        # Nombre del proyecto (fila destacada)
        f2 = QFont("Segoe UI", 12)
        f2.setBold(True)
        p.setFont(f2)
        p.setPen(QPen(QColor("#1a237e"), 1))
        proyecto = meta.get("proyecto") or "PROYECTO"
        p.drawText(QRectF(bx + 4, by + header_h, bw - 8, 22),
                   Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                   proyecto)

        # Variables de celda
        thin = QPen(QColor("#90a4ae"), 1)
        yy = by + header_h + 22
        row_h = 26

        def _cell(label: str, value: str, x: float, cw: float,
                  rh: float) -> None:
            lf = QFont("Segoe UI", 8)
            lf.setBold(True)
            p.setFont(lf)
            p.setPen(QPen(QColor("#0d47a1"), 1))
            p.drawText(QRectF(x + 3, yy + 1, cw - 6, 12),
                       Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                       label)
            p.setFont(QFont("Segoe UI", 9))
            p.setPen(QPen(QColor("#1a237e"), 1))
            p.drawText(QRectF(x + 3, yy + 12, cw - 6, rh - 12),
                       Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                       value or "")
            p.setPen(thin)
            p.drawLine(x, yy + rh, x + cw, yy + rh)
            p.drawLine(x + cw, yy, x + cw, yy + rh)

        c1 = int(bw * 0.50)
        c2 = int(bw * 0.28)
        c3 = bw - c1 - c2

        _cell("CLIENTE", meta.get("cliente"), bx, c1, row_h)
        _cell("ESCALA", meta.get("escala"), bx + c1, c2, row_h)
        _cell("FECHA", meta.get("fecha"), bx + c1 + c2, c3, row_h)
        yy += row_h

        _cell("DISEÑO / AUTOR", meta.get("autor"), bx, c1, row_h)
        _cell("PLANO Nº", meta.get("plano"), bx + c1, c2, row_h)
        _cell("REV", meta.get("revision"), bx + c1 + c2, c3, row_h)
        yy += row_h

        _cell("EMPRESA", meta.get("empresa"), bx, c1, row_h)
        _cell("FORMATO", f"{int(w)}×{int(h)}", bx + c1, c2, row_h)
        _cell("FECHA PROY", meta.get("fecha"), bx + c1 + c2, c3, row_h)

        p.restore()
