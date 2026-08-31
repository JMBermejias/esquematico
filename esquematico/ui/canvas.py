"""Lienzo interactivo para editar el esquema eléctrico.

Permite colocar símbolos, moverlos, rotarlos, redimensionarlos y conectar
cables entre los pines de conexión de cada símbolo.
"""

from __future__ import annotations

import math
from typing import Dict, List, Optional

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen, QWheelEvent
from PySide6.QtWidgets import (
    QAbstractItemView,
    QGraphicsItem,
    QGraphicsEllipseItem,
    QGraphicsLineItem,
    QGraphicsPathItem,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsSceneMouseEvent,
    QGraphicsSimpleTextItem,
    QGraphicsView,
    QMenu,
)

from ..core.model import Diagram, SymbolInstance, Wire
from ..core.renderer import DiagramRenderer
from ..symbols.library import Symbol


class DiagramScene(QGraphicsScene):
    """Escena que dibuja el diagrama mediante el renderer."""

    def __init__(self, diagram: Diagram, symbol_lookup: Dict[str, Symbol],
                 parent=None) -> None:
        super().__init__(parent)
        self.diagram = diagram
        self.symbol_lookup = symbol_lookup
        self.show_grid = True
        self.show_pins = True

    def drawBackground(self, painter: QPainter, rect: QRectF) -> None:
        renderer = DiagramRenderer(painter, self.diagram, self.symbol_lookup)
        renderer.draw_background()
        renderer.draw_sheet()
        renderer.draw_title_block()


class DiagramView(QGraphicsView):
    """Vista del lienzo con interacción de usuario."""

    zoom_changed = Signal(float)
    symbol_selected = Signal(object)  # SymbolInstance | None
    status_message = Signal(str)

    def __init__(self, diagram: Diagram, symbol_lookup: Dict[str, Symbol],
                 parent=None) -> None:
        super().__init__(parent)
        self.diagram = diagram
        self.symbol_lookup = symbol_lookup

        self.scene = DiagramScene(diagram, symbol_lookup, self)
        self.scene.setSceneRect(
            QRectF(-200, -200, diagram.width + 400, diagram.height + 400)
        )
        self.setScene(self.scene)
        self.setBackgroundBrush(QColor("#ffffff"))
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)

        # Estado de la herramienta
        self.tool = "select"          # select | symbol | wire | pan
        self.pending_symbol: Optional[SymbolInstance] = None
        self.wire_start: Optional[QPointF] = None
        self.wire_start_pos: Optional[QPointF] = None
        self.wire_preview_start: Optional[QPointF] = None
        self._snapping = True
        self._zoom = 1.0

        # Cache de pines documental (para conectar)
        self._pin_positions: Dict[str, List[QPointF]] = {}

        # Caché de render (elementos gráficos propios de los símbolos)
        self._symbol_items: Dict[int, QGraphicsItem] = {}
        self._wire_items: Dict[int, QGraphicsLineItem] = {}
        self._grid_dots: List[QGraphicsEllipseItem] = []
        self._pending_preview_item = None
        self._wire_preview_line: Optional[QGraphicsLineItem] = None
        self._wire_start_marker: Optional[QGraphicsEllipseItem] = None
        self._wire_dragging = False

        self._rebuild_static()
        self._update_pin_cache()

    # ------------------------------------------------------------------
    # Render primitivo: dibujamos los símbolos como items gráficos
    # ------------------------------------------------------------------
    def _rebuild_static(self) -> None:
        self.scene.clear()
        self._symbol_items.clear()
        self._wire_items.clear()
        self._grid_dots.clear()
        self._pending_preview_item = None
        self._wire_preview_line = None

        # Cables
        for w in self.diagram.wires:
            self._make_wire_item(w)

        # Símbolos
        for inst in self.diagram.symbols:
            item = SymbolItem(inst, self.symbol_lookup, self)
            item.setZValue(10)
            self.scene.addItem(item)
            self._symbol_items[id(inst)] = item

        self._rebuild_grid_dots()

    def _rebuild_grid_dots(self) -> None:
        """Crea los puntos de la cuadrícula como elementos reales de la escena
        (tamaño fijo en pantalla, visibles a cualquier zoom)."""
        for d in self._grid_dots:
            try:
                self.scene.removeItem(d)
            except RuntimeError:
                pass
        self._grid_dots.clear()
        if not self.scene.show_grid:
            return
        g = self.diagram.grid_size
        w, h = self.diagram.width, self.diagram.height
        r = 3.0
        x = 0.0
        while x <= w:
            y = 0.0
            while y <= h:
                dot = QGraphicsEllipseItem(QRectF(-r, -r, 2 * r, 2 * r))
                dot.setPos(x, y)
                dot.setBrush(QColor("#6d6d6d"))
                dot.setPen(Qt.PenStyle.NoPen)
                dot.setZValue(0)
                dot.setFlag(
                    QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations,
                    True)
                dot.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
                self.scene.addItem(dot)
                self._grid_dots.append(dot)
                y += g
            x += g

    def set_grid_visible(self, visible: bool) -> None:
        self.scene.show_grid = visible
        self._rebuild_grid_dots()
        self.scene.update()

    def _make_wire_item(self, w: Wire) -> QGraphicsLineItem:
        item = WireItem(w, self)
        self.scene.addItem(item)
        self._wire_items[id(w)] = item
        return item

    def _update_pin_cache(self) -> None:
        """Recalcula posiciones absolutas de los pines de cada símbolo."""
        self._pin_positions.clear()
        for inst in self.diagram.symbols:
            try:
                symbol = self.symbol_lookup[inst.symbol_id]
            except KeyError:
                continue
            pins = []
            for prim in symbol.primitives:
                if prim.kind == "pin":
                    px, py = inst.x + prim.args[0] * inst.scale, \
                             inst.y + prim.args[1] * inst.scale
                    px, py = _rotate_point(px, py, inst.x, inst.y, inst.rotation)
                    pins.append(QPointF(px, py))
            self._pin_positions[id(inst)] = pins

    def nearest_pin(self, pos: QPointF, max_dist: float = 14.0
                    ) -> Optional[QPointF]:
        best, best_d = None, max_dist
        for inst in self.diagram.symbols:
            for pin in self._pin_positions.get(id(inst), []):
                d = math.hypot(pin.x() - pos.x(), pin.y() - pos.y())
                if d < best_d:
                    best, best_d = pin, d
        return best

    # ------------------------------------------------------------------
    # Herramientas
    # ------------------------------------------------------------------
    def set_tool(self, tool: str) -> None:
        self.tool = tool
        if self.pending_symbol is not None:
            self._remove_pending()
        if tool == "pan":
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        elif tool == "select":
            self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        else:
            self.setDragMode(QGraphicsView.DragMode.NoDrag)

    def set_symbol(self, symbol: Symbol) -> None:
        self.pending_symbol = SymbolInstance(symbol.id, 0, 0)
        self.tool = "symbol"
        self.setDragMode(QGraphicsView.DragMode.NoDrag)

    def _remove_pending(self) -> None:
        if self._pending_preview_item is not None:
            self.scene.removeItem(self._pending_preview_item)
            self._pending_preview_item = None
        self.pending_symbol = None
        self.symbol_selected.emit(None)

    def snap(self, p: QPointF) -> QPointF:
        if not self._snapping:
            return p
        g = self.diagram.grid_size
        return QPointF(round(p.x() / g) * g, round(p.y() / g) * g)

    def add_symbol_at(self, pos: QPointF, symbol: Symbol) -> SymbolInstance:
        p = self.snap(pos)
        inst = SymbolInstance(symbol.id, p.x(), p.y())
        self.diagram.add_symbol(inst)
        item = SymbolItem(inst, self.symbol_lookup, self)
        item.setZValue(10)
        self.scene.addItem(item)
        self._symbol_items[id(inst)] = item
        self._update_pin_cache()
        return inst

    def start_wire(self, pos: QPointF) -> None:
        self.wire_start = self.snap(pos)
        self.wire_start_pos = self.wire_start
        self.wire_preview_start = self.wire_start
        # Marca visible del punto inicial
        marker = QGraphicsEllipseItem(
            self.wire_start.x() - 5, self.wire_start.y() - 5, 10, 10)
        marker.setBrush(QColor("#2f80ed"))
        marker.setPen(QPen(QColor("#0d47a1"), 1))
        marker.setZValue(6)
        self.scene.addItem(marker)
        self._wire_start_marker = marker
        # Línea de guía (se hará visible al mover el ratón)
        pen = QPen(QColor("#1a73e8"), 2)
        pen.setStyle(Qt.PenStyle.DashLine)
        self._wire_preview_line = self.scene.addLine(
            self.wire_start.x(), self.wire_start.y(),
            self.wire_start.x(), self.wire_start.y(), pen)
        self._wire_preview_line.setZValue(5)
        self.status_message.emit(
            "Punto inicial del cable: arrastre al punto final")

    def update_wire_preview(self, pos: QPointF) -> None:
        if self._wire_preview_line is not None and self.wire_start is not None:
            p = self.snap(pos)
            self._wire_preview_line.setLine(
                self.wire_start.x(), self.wire_start.y(), p.x(), p.y())

    def finish_wire(self, pos: QPointF) -> None:
        if self.wire_start is not None:
            end = self.snap(pos)
            # Si no hay desplazamiento, no crear un cable de longitud cero
            if (end.x() != self.wire_start.x()
                    or end.y() != self.wire_start.y()):
                w = Wire(self.wire_start.x(), self.wire_start.y(),
                         end.x(), end.y())
                self.diagram.add_wire(w)
                self._make_wire_item(w)
                self.status_message.emit("Cable creado")
        self._clear_wire_state()

    def _clear_wire_state(self) -> None:
        if self._wire_preview_line is not None:
            self.scene.removeItem(self._wire_preview_line)
            self._wire_preview_line = None
        if self._wire_start_marker is not None:
            self.scene.removeItem(self._wire_start_marker)
            self._wire_start_marker = None
        self.wire_start = None
        self.wire_start_pos = None
        self._wire_dragging = False

    def cancel_wire(self) -> None:
        self._clear_wire_state()
        self.status_message.emit("Cable cancelado")

    def set_pending_preview(self, pos: QPointF, symbol: Symbol) -> None:
        if self._pending_preview_item is not None:
            self.scene.removeItem(self._pending_preview_item)
        p = self.snap(pos)
        inst = SymbolInstance(symbol.id, 0, 0)
        # Crear item temporal con posición en p
        inst.x, inst.y = p.x(), p.y()
        item = SymbolItem(inst, self.symbol_lookup, self, transient=True)
        item.setZValue(20)
        item.setOpacity(0.5)
        self.scene.addItem(item)
        self._pending_preview_item = item

    def update_pending_preview(self, pos: QPointF) -> None:
        if self._pending_preview_item is not None:
            p = self.snap(pos)
            self._pending_preview_item.setPos(p.x(), p.y())

    def mouse_canvas_pos(self, event) -> QPointF:
        try:
            return self.mapToScene(event.position().toPoint())
        except AttributeError:
            return self.mapToScene(event.pos())

    def clear_selection(self) -> None:
        self.scene.clearSelection()
        self.symbol_selected.emit(None)

    # ------------------------------------------------------------------
    # Eventos de ratón
    # ------------------------------------------------------------------
    def mousePressEvent(self, event) -> None:
        pos = self.mouse_canvas_pos(event)

        if self.tool == "symbol" and self.pending_symbol is not None:
            if event.button() == Qt.MouseButton.RightButton:
                self._remove_pending()
                self.status_message.emit("Colocación cancelada")
                return
            symbol = self.symbol_lookup.get(self.pending_symbol.symbol_id)
            if symbol and event.button() == Qt.MouseButton.LeftButton:
                inst = self.add_symbol_at(pos, symbol)
                self._update_pin_cache()
                self.status_message.emit(f"Colocado: {symbol.name}")
                self.symbol_selected.emit(inst)
            return

        if self.tool == "wire":
            if event.button() == Qt.MouseButton.RightButton:
                if self.wire_start is not None:
                    self.cancel_wire()
                return
            if event.button() == Qt.MouseButton.LeftButton:
                if self.wire_start is None:
                    p = self.nearest_pin(pos)
                    self.start_wire(p if p else pos)
                    self._wire_dragging = False
                else:
                    # Segundo clic sin arrastre: finalizar (modelo clic-clic)
                    if not self._wire_dragging:
                        p = self.nearest_pin(pos)
                        self.finish_wire(p if p else pos)
                        self._update_pin_cache()
            return

        if self.tool == "select" and event.button() == Qt.MouseButton.LeftButton:
            item = self.itemAt(pos)
            if item is not None and item.data(0) == "wire":
                self.select_wire(item.data(1))
                return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        pos = self.mouse_canvas_pos(event)
        if self.tool == "symbol" and self.pending_symbol is not None:
            symbol = self.symbol_lookup.get(self.pending_symbol.symbol_id)
            if symbol is None:
                return
            if self._pending_preview_item is None:
                self.set_pending_preview(pos, symbol)
            else:
                self.update_pending_preview(pos)
            return
        if self.tool == "wire" and self.wire_start is not None:
            if event.buttons() & Qt.MouseButton.LeftButton:
                self._wire_dragging = True
            self.update_wire_preview(pos)
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if (self.tool == "wire" and self.wire_start is not None
                and self._wire_dragging
                and event.button() == Qt.MouseButton.LeftButton):
            pos = self.mouse_canvas_pos(event)
            p = self.nearest_pin(pos)
            self.finish_wire(p if p else pos)
            self._update_pin_cache()
            return
        super().mouseReleaseEvent(event)

    def wheelEvent(self, event: QWheelEvent) -> None:
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        new_zoom = max(0.2, min(5.0, self._zoom * factor))
        if new_zoom != self._zoom:
            self._zoom = new_zoom
            self.scale(factor, factor)
            self.zoom_changed.emit(self._zoom)

    def find_symbol_at(self, pos: QPointF) -> Optional[SymbolInstance]:
        item = self.itemAt(pos)
        if isinstance(item, SymbolItem):
            return item.inst
        return None

    def find_wire_at(self, pos: QPointF) -> Optional[Wire]:
        item = self.itemAt(pos)
        if item is not None and item.data(0) == "wire":
            return item.data(1)
        return None

    def delete_selected(self) -> None:
        removed_any = False
        for it in list(self.scene.selectedItems()):
            if isinstance(it, SymbolItem):
                inst = it.inst
                if inst in self.diagram.symbols:
                    self.diagram.symbols.remove(inst)
                self.scene.removeItem(it)
                self._symbol_items.pop(id(inst), None)
                removed_any = True
            elif it.data(0) == "wire":
                w = it.data(1)
                if w in self.diagram.wires:
                    self.diagram.wires.remove(w)
                self.scene.removeItem(it)
                self._wire_items.pop(id(w), None)
                removed_any = True
        if removed_any:
            self._update_pin_cache()
            self.symbol_selected.emit(None)
            self.status_message.emit("Elemento(s) eliminados")

    def select_symbol(self, inst: Optional[SymbolInstance]) -> None:
        for it in self.scene.items():
            if isinstance(it, SymbolItem):
                it.setSelected(it.inst is inst)
        self.symbol_selected.emit(inst)

    def select_wire(self, w: Optional[Wire]) -> None:
        for it in self.scene.items():
            if it.data(0) == "wire":
                it.setSelected(it.data(1) is w)
        self.symbol_selected.emit(None)

    def remove_symbol(self, inst: SymbolInstance) -> None:
        if inst in self.diagram.symbols:
            self.diagram.symbols.remove(inst)
        it = self._symbol_items.pop(id(inst), None)
        if it is not None:
            self.scene.removeItem(it)
        self._update_pin_cache()
        self.symbol_selected.emit(None)

    def refresh(self) -> None:
        self._rebuild_static()
        self._update_pin_cache()
        self.scene.update()


def _rotate_point(x: float, y: float, cx: float, cy: float,
                  rotation: float):
    if rotation == 0:
        return x, y
    rad = math.radians(rotation)
    cos, sin = math.cos(rad), math.sin(rad)
    dx, dy = x - cx, y - cy
    return cx + dx * cos - dy * sin, cy + dx * sin + dy * cos


class WireItem(QGraphicsLineItem):
    """Item de cable que se resalta al ser seleccionado."""

    def __init__(self, w: Wire, view: "DiagramView") -> None:
        super().__init__(w.x1, w.y1, w.x2, w.y2)
        self.wire = w
        self.view = view
        pen = QPen(QColor(w.color), w.width)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        self._base_pen = pen
        self.setPen(pen)
        self.setZValue(1)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setData(0, "wire")
        self.setData(1, w)

    def paint(self, painter: QPainter, option, widget=None) -> None:
        if self.isSelected():
            sel_pen = QPen(QColor("#2196f3"), self._base_pen.width() + 3)
            sel_pen.setStyle(Qt.PenStyle.DashLine)
            sel_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.save()
            painter.setPen(sel_pen)
            painter.drawLine(self.line())
            painter.restore()
        painter.setPen(self._base_pen)
        painter.drawLine(self.line())


class SymbolItem(QGraphicsItem):
    """Item gráfico que representa un símbolo y permite mover/rotar/redimensionar."""

    def __init__(self, inst: SymbolInstance, lookup: Dict[str, Symbol],
                 view: "DiagramView", transient: bool = False) -> None:
        super().__init__()
        self.inst = inst
        self.lookup = lookup
        self.view = view
        self.transient = transient
        self._follow = None
        symbol = lookup.get(inst.symbol_id)
        self._symbol = symbol
        half_w = (symbol.width / 2.0 if symbol else 25) * inst.scale
        half_h = (symbol.height / 2.0 if symbol else 25) * inst.scale
        if self.inst.rotation != 0:
            rad = math.radians(self.inst.rotation)
            ca, sa = abs(math.cos(rad)), abs(math.sin(rad))
            half_w, half_h = half_w * ca + half_h * sa, half_w * sa + half_h * ca
        self._half_w = half_w
        self._half_h = half_h
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, not transient)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, not transient)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges,
                     not transient)
        self.setPos(inst.x, inst.y)

    def boundingRect(self) -> QRectF:
        pad = 12
        return QRectF(-self._half_w - pad, -self._half_h - pad,
                      (self._half_w + pad) * 2, (self._half_h + pad) * 2)

    def paint(self, painter: QPainter, option, widget=None) -> None:
        symbol = self._symbol
        if symbol is None:
            return
        painter.save()
        r = painter
        color = QColor(self.inst.color)
        pen = QPen(color, 2.0)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        r.setPen(pen)
        r.setBrush(Qt.BrushStyle.NoBrush)

        scale = self.inst.scale

        # Selección
        if self.isSelected():
            sel_pen = QPen(QColor("#2196f3"), 1.5)
            sel_pen.setStyle(Qt.PenStyle.DashLine)
            r.setPen(sel_pen)
            r.setBrush(Qt.BrushStyle.NoBrush)
            r.drawRect(QRectF(-self._half_w - 6, -self._half_h - 6,
                              self._half_w * 2 + 12, self._half_h * 2 + 12))
            r.setPen(pen)

        for prim in symbol.primitives:
            kind = prim.kind
            args = prim.args
            _stylecolor = prim.style.get("color", self.inst.color)
            if kind == "line":
                r.setPen(QPen(QColor(_stylecolor), 2.0))
                r.setBrush(Qt.BrushStyle.NoBrush)
                r.drawLine(QPointF(args[0] * scale, args[1] * scale),
                           QPointF(args[2] * scale, args[3] * scale))
            elif kind == "circle":
                cx0, cy0 = args[0] * scale, args[1] * scale
                rad = args[2] * scale
                r.setPen(QPen(QColor(_stylecolor), 2.0))
                if prim.style.get("filled"):
                    r.setBrush(color)
                else:
                    r.setBrush(Qt.BrushStyle.NoBrush)
                r.drawEllipse(QRectF(cx0 - rad, cy0 - rad, 2 * rad, 2 * rad))
                r.setBrush(Qt.BrushStyle.NoBrush)
            elif kind == "rect":
                r.setPen(QPen(QColor(_stylecolor), 2.0))
                r.setBrush(Qt.BrushStyle.NoBrush)
                rect = QRectF(args[0] * scale, args[1] * scale,
                              args[2] * scale, args[3] * scale)
                if prim.style.get("rounded"):
                    r.drawRoundedRect(rect, 8, 8)
                elif prim.style.get("panel"):
                    r.drawRect(rect)
                else:
                    r.drawRect(rect)
            elif kind == "text":
                text = str(prim.style.get("text", args[2] if len(args) > 2 else ""))
                f = r.font()
                f.setPointSizeF(int(prim.style.get("size", 14)))
                if prim.style.get("bold"):
                    f.setBold(True)
                r.setFont(f)
                r.setPen(QPen(QColor(_stylecolor), 1))
                r.drawText(QPointF(args[0] * scale, args[1] * scale), text)
            elif kind == "pin":
                px, py = args[0] * scale, args[1] * scale
                r.setBrush(QColor("#2f80ed"))
                r.setPen(QPen(QColor("#2f80ed"), 1))
                r.drawEllipse(QPointF(px, py), 3, 3)
                r.setBrush(Qt.BrushStyle.NoBrush)

        # Etiqueta
        if self.inst.label and not self.transient:
            f = r.font()
            f.setPointSizeF(10)
            f.setBold(True)
            r.setFont(f)
            r.setPen(QPen(QColor("#1565c0"), 1))
            r.drawText(QPointF(-60, self._half_h + 16), self.inst.label)

        painter.restore()

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged \
                and not self.transient:
            # Aplicar snapping al mover
            g = self.view.diagram.grid_size
            p = value
            p.setX(round(p.x() / g) * g)
            p.setY(round(p.y() / g) * g)
            self.inst.x, self.inst.y = p.x(), p.y()
            self.setPos(p)
            self.view._update_pin_cache()
            return p
        return super().itemChange(change, value)

    def mouseDoubleClickEvent(self, event) -> None:
        if self.view.tool == "select":
            # Rotar 90 grados al hacer doble clic
            self.inst.rotation = (self.inst.rotation + 90) % 360
            self.update_shape()
            self.view._update_pin_cache()
            self.update()
        super().mouseDoubleClickEvent(event)

    def update_shape(self) -> None:
        half_w = (self._symbol.width / 2.0 if self._symbol else 25) * self.inst.scale
        half_h = (self._symbol.height / 2.0 if self._symbol else 25) * self.inst.scale
        if self.inst.rotation != 0:
            rad = math.radians(self.inst.rotation)
            ca, sa = abs(math.cos(rad)), abs(math.sin(rad))
            half_w, half_h = half_w * ca + half_h * sa, half_w * sa + half_h * ca
        self._half_w = max(half_w, 14)
        self._half_h = max(half_h, 14)
        self.prepareGeometryChange()

    def contextMenuEvent(self, event) -> None:
        if self.transient:
            return
        menu = QMenu()
        act_rot90 = menu.addAction("Rotar 90°")
        act_del = menu.addAction("Eliminar")
        act_dup = menu.addAction("Duplicar")
        chosen = menu.exec(event.screenPos())
        if chosen == act_del:
            self.view.remove_symbol(self.inst)
        elif chosen == act_rot90:
            self.inst.rotation = (self.inst.rotation + 90) % 360
            self.update_shape()
            self.view._update_pin_cache()
            self.update()
        elif chosen == act_dup:
            import copy
            new_inst = copy.deepcopy(self.inst)
            new_inst.x += 40
            new_inst.y += 40
            self.view.diagram.add_symbol(new_inst)
            item = SymbolItem(new_inst, self.lookup, self.view)
            item.setZValue(10)
            self.view.scene.addItem(item)
            self.view._symbol_items[id(new_inst)] = item
            self.view._update_pin_cache()
