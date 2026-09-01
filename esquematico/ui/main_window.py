"""Ventana principal de la aplicación Esquemático."""

from __future__ import annotations

import os
from typing import Dict, Optional

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QAction, QActionGroup, QColor, QKeySequence, QPainter
from PySide6.QtWidgets import (
    QDockWidget,
    QFileDialog,
    QGraphicsView,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QStatusBar,
    QTabWidget,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from .. import __appname__, __version__
from ..core.history import History
from ..core.model import Diagram, SymbolInstance
from ..symbols.library import Symbol, build_library, symbol_by_id
from .canvas import DiagramView
from .palette import SymbolPalette
from .project_dialog import ProjectDialog
from .properties import PropertiesPanel

STYLE = """
QMainWindow, QWidget {
    background-color: #eaf2fc;
    color: #1a237e;
    font-family: 'Segoe UI';
    font-size: 12px;
}
QToolBar {
    background-color: #bcd9f6;
    border: none;
    spacing: 4px;
    padding: 4px;
}
QToolBar QToolButton {
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: 6px;
    padding: 6px;
    font-weight: bold;
    color: #0d47a1;
}
QToolBar QToolButton:hover {
    background-color: #d7e9fb;
    border-color: #90b8e0;
}
QToolBar QToolButton:checked {
    background-color: #2f80ed;
    color: white;
}
QDockWidget {
    titlebar-close-icon: none;
}
QDockWidget::title {
    background-color: #bcd9f6;
    padding: 4px 8px;
    font-weight: bold;
    color: #0d47a1;
}
#panelTitle {
    font-size: 14px;
    font-weight: bold;
    color: #0d47a1;
}
QListWidget#symbolList {
    background-color: #ffffff;
    border: 1px solid #bcd9f6;
    border-radius: 6px;
    outline: none;
}
QListWidget#symbolList::item {
    padding: 4px;
    border-bottom: 1px solid #e0eeff;
}
QListWidget#symbolList::item:hover {
    background-color: #d7e9fb;
}
QListWidget#symbolList::item:selected {
    background-color: #2f80ed;
    color: white;
}
QLineEdit, QComboBox, QDoubleSpinBox {
    background-color: #ffffff;
    border: 1px solid #bcd9f6;
    border-radius: 5px;
    padding: 4px;
    color: #1a237e;
    selection-background-color: #2f80ed;
}
QLineEdit:focus, QComboBox:focus, QDoubleSpinBox:focus {
    border-color: #2f80ed;
}
QPushButton {
    background-color: #2f80ed;
    color: white;
    border: none;
    border-radius: 5px;
    padding: 6px 12px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #1a6fe0;
}
QPushButton:disabled {
    background-color: #a9c6e8;
}
QStatusBar {
    background-color: #bcd9f6;
    color: #0d47a1;
}
QMenuBar {
    background-color: #bcd9f6;
    color: #0d47a1;
}
QMenuBar::item:selected {
    background-color: #2f80ed;
    color: white;
}
QMenu {
    background-color: #ffffff;
    color: #1a237e;
    border: 1px solid #bcd9f6;
}
QMenu::item:selected {
    background-color: #d7e9fb;
}
QScrollBar:vertical {
    background: #eaf2fc;
    width: 12px;
}
QScrollBar::handle:vertical {
    background: #90b8e0;
    border-radius: 6px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover { background: #2f80ed; }
QScrollBar::add-line, QScrollBar::sub-line { height: 0; }
"""


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.library: Dict[str, Symbol] = {s.id: s for s in build_library()}
        self.diagram = Diagram()
        self.current_path: Optional[str] = None

        self.history = History(self.diagram)

        self.setWindowTitle(f"{__appname__} - {self.diagram.name}")
        self.resize(1280, 800)
        self.setStyleSheet(STYLE)
        self.showMaximized()

        self._build_central()
        self._build_docks()
        self._build_menus()
        self._build_toolbar()
        self.statusBar().showMessage("Listo")

        self._update_title()

    # ------------------------------------------------------------------
    # Construcción de UI
    # ------------------------------------------------------------------
    def _build_menus(self) -> None:
        mbar = self.menuBar()

        m_archivo = mbar.addMenu("&Archivo")
        m_archivo.addAction(self._action("Nuevo", self.new_document,
                                         "Ctrl+N"))
        m_archivo.addAction(self._action("Abrir...", self.open_document,
                                         "Ctrl+O"))
        m_archivo.addSeparator()
        m_archivo.addAction(self._action("Guardar", self.save_document,
                                         "Ctrl+S"))
        m_archivo.addAction(self._action("Guardar como...",
                                         self.save_document_as, "Ctrl+Shift+S"))
        m_archivo.addSeparator()
        m_archivo.addAction(self._action("Exportar PNG...", self.export_png))
        m_archivo.addAction(self._action("Exportar PDF...", self.export_pdf))
        m_archivo.addSeparator()
        m_archivo.addAction(self._action("Salir", self.close, "Alt+F4"))

        m_editar = mbar.addMenu("&Editar")
        self.act_undo = self._action("Deshacer", self.undo, "Ctrl+Z")
        self.act_redo = self._action("Rehacer", self.redo,
                                     "Ctrl+Y", )
        self.act_redo.setShortcuts([QKeySequence("Ctrl+Y"),
                                    QKeySequence("Ctrl+Shift+Z")])
        self.act_undo.setEnabled(False)
        self.act_redo.setEnabled(False)
        self.history.changed.connect(self._update_history_actions)
        m_editar.addAction(self.act_undo)
        m_editar.addAction(self.act_redo)
        m_editar.addSeparator()
        m_editar.addAction(self._action("Limpiar todo", self.clear_all))
        m_editar.addSeparator()
        m_editar.addAction(self._action("Eliminar selección",
                                        self.view.delete_selected, "Supr"))
        m_editar.addAction(self._action("Rotar 90° selección",
                                        self.rotate_selected, "R"))

        m_proyecto = mbar.addMenu("&Proyecto")
        m_proyecto.addAction(self._action("Datos del proyecto...",
                                          self.project_data))

        m_ver = mbar.addMenu("&Ver")
        self.act_grid = self._action("Mostrar cuadrícula", self.toggle_grid,
                                     checkable=True)
        self.act_grid.setChecked(True)
        self.act_pins = self._action("Mostrar puntos de conexión",
                                     self.toggle_pins, checkable=True)
        self.act_pins.setChecked(True)
        m_ver.addAction(self.act_grid)
        m_ver.addAction(self.act_pins)
        m_ver.addSeparator()
        m_ver.addAction(self._action("Acercar", lambda: self.zoom_view(1.2),
                                     "Ctrl++"))
        m_ver.addAction(self._action("Alejar", lambda: self.zoom_view(1 / 1.2),
                                     "Ctrl+-"))
        m_ver.addAction(self._action("Ajustar a la ventana",
                                     self.fit_view, "Ctrl+0"))

        m_ayuda = mbar.addMenu("&Ayuda")
        m_ayuda.addAction(self._action("Acerca de", self.about))

    def _action(self, text, slot=None, shortcut=None, checkable=False) -> QAction:
        act = QAction(text, self)
        act.setCheckable(checkable)
        if shortcut:
            act.setShortcut(QKeySequence(shortcut))
        if slot:
            act.triggered.connect(slot)
        return act

    def _build_toolbar(self) -> None:
        tb = QToolBar("Herramientas")
        tb.setMovable(False)
        tb.setIconSize(QSize(20, 20))
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, tb)

        # Grupo exclusivo de herramientas: al pulsar una se resalta
        self._tool_actions: Dict[str, QAction] = {}
        self.tool_group = QActionGroup(self)
        self.tool_group.setExclusive(True)

        def _tool_action(text, tool, shortcut=None):
            act = self._action(text, lambda: self.set_tool(tool), shortcut,
                               checkable=True)
            self.tool_group.addAction(act)
            self.tool_group.setExclusive(True)
            self._tool_actions[tool] = act
            tb.addAction(act)
            return act

        _tool_action("Seleccionar", "select", "V")
        _tool_action("Símbolo", "symbol_prompt", "S")
        tb.addSeparator()
        _tool_action("Cable", "wire", "C")
        tb.addSeparator()
        _tool_action("Mano", "pan", "H")
        tb.addSeparator()
        tb.addAction(self.act_undo)
        tb.addAction(self.act_redo)
        tb.addSeparator()
        tb.addAction(self._action("Limpiar", self.clear_all))
        tb.addSeparator()
        tb.addAction(self._action("- zoom", lambda: self.zoom_view(1 / 1.2)))
        tb.addAction(self._action("+ zoom", lambda: self.zoom_view(1.2)))
        tb.addSeparator()
        # Puntos de referencia de la cuadrícula: mostrar/ocultar con un clic
        act = self._action("Puntos de cuadrícula", self.toggle_grid,
                           checkable=True)
        act.setChecked(True)
        self.act_grid.setChecked(True)
        tb.addAction(act)

        # Herramienta por defecto
        self._tool_actions["select"].setChecked(True)

    def _build_central(self) -> None:
        self.view = DiagramView(self.diagram, self.library)
        self.view.history = self.history
        self.view.symbol_selected.connect(self._on_symbol_selected)
        self.view.status_message.connect(self.statusBar().showMessage)

        self.right_dock = QTabWidget()
        self.right_dock.setObjectName("rightTabs")

        container = QWidget()
        v = QVBoxLayout(container)
        v.setContentsMargins(0, 0, 0, 0)
        v.addWidget(self.view, 1)
        self.zoom_label = QLabel("100%")
        self.zoom_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        v.addWidget(self.zoom_label)
        self.view.zoom_changed.connect(self._on_zoom)
        self.setCentralWidget(container)

    def _build_docks(self) -> None:
        self.palette = SymbolPalette(list(self.library.values()))
        self.palette.symbol_activated.connect(self._palette_symbol_selected)
        dock_palette = QDockWidget("Biblioteca", self)
        dock_palette.setWidget(self.palette)
        dock_palette.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetFloatable
                                 | QDockWidget.DockWidgetFeature.DockWidgetMovable)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, dock_palette)

        self.props = PropertiesPanel()
        self.props.changed.connect(self._on_props_changed)
        self.props.edit_started.connect(self.history.checkpoint)
        self.props.edit_finished.connect(self._on_props_edit_finished)
        dock_props = QDockWidget("Propiedades", self)
        dock_props.setWidget(self.props)
        dock_props.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetFloatable
                               | QDockWidget.DockWidgetFeature.DockWidgetMovable)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock_props)

    # ------------------------------------------------------------------
    # Herramientas
    # ------------------------------------------------------------------
    def set_tool(self, tool: str) -> None:
        # Resalta el botón de la herramienta activa
        if tool in self._tool_actions:
            self._tool_actions[tool].setChecked(True)
        if tool == "symbol_prompt":
            self.view.set_tool("symbol")
            self.statusBar().showMessage(
                "Elija un símbolo en la biblioteca (izquierda) y haga clic "
                "en el lienzo para colocarlo")
            return
        self.view.set_tool(tool)
        self.statusBar().showMessage(
            {"select": "Herramienta: seleccionar (clic para elegir, "
                       "arrastrar para mover)",
             "wire": "Herramienta: cable (1er clic: inicio, 2º clic: fin)",
             "pan": "Herramienta: mano (arrastrar para desplazar)",
             "symbol": "Haga clic en el lienzo para colocar el símbolo"
             }.get(tool, ""))

    def prompt_symbol(self) -> None:
        self.set_tool("symbol_prompt")

    def _palette_symbol_selected(self, symbol: Symbol) -> None:
        """Arma el símbolo elegido en la biblioteca para colocarlo en el lienzo."""
        if "symbol_prompt" in self._tool_actions:
            self._tool_actions["symbol_prompt"].setChecked(True)
        self.view.set_symbol(symbol)
        self.statusBar().showMessage(
            f"Coloque el símbolo «{symbol.name}» haciendo clic en el lienzo "
            "(clic con el botón derecho cancela)")

    def toggle_grid(self) -> None:
        self.view.set_grid_visible(self.act_grid.isChecked())

    def toggle_pins(self) -> None:
        self.view.scene.show_pins = self.act_pins.isChecked()
        self.view.refresh()

    def zoom_view(self, factor: float) -> None:
        self.view.scale(factor, factor)
        self.view.zoom_changed.emit(self.view._zoom * factor)
        self.view._zoom *= factor

    def _on_zoom(self, z: float) -> None:
        self.zoom_label.setText(f"{int(z * 100)}%")

    def fit_view(self) -> None:
        self.view.fitInView(self.view.scene.sceneRect(),
                            Qt.AspectRatioMode.KeepAspectRatio)

    def rotate_selected(self) -> None:
        self.history.checkpoint()
        for it in self.view.scene.selectedItems():
            from .canvas import SymbolItem
            if isinstance(it, SymbolItem):
                it.inst.rotation = (it.inst.rotation + 90) % 360
                it.update_shape()
        if self.view.scene.selectedItems():
            self.history.commit()
        self.view._update_pin_cache()
        self.props.set_symbol(self._current_selected())

    # ------------------------------------------------------------------
    # Selección
    # ------------------------------------------------------------------
    def _current_selected(self) -> Optional[SymbolInstance]:
        for it in self.view.scene.selectedItems():
            from .canvas import SymbolItem
            if isinstance(it, SymbolItem):
                return it.inst
        return None

    def _on_symbol_selected(self, inst: Optional[SymbolInstance]) -> None:
        self.props.set_symbol(inst)
        if inst is not None:
            try:
                s = self.library[inst.symbol_id]
                inst._symbol_name = s.name
            except KeyError:
                inst._symbol_name = inst.symbol_id

    def _on_props_changed(self) -> None:
        self.view._update_pin_cache()
        for it in self.view.scene.selectedItems():
            from .canvas import SymbolItem
            if isinstance(it, SymbolItem):
                it.update()
                it.update_shape()

    def _on_props_edit_finished(self) -> None:
        self.history.commit()
        self.view._update_pin_cache()

    # ------------------------------------------------------------------
    # Deshacer / rehacer / limpiar
    # ------------------------------------------------------------------
    def _update_history_actions(self) -> None:
        self.act_undo.setEnabled(self.history.can_undo())
        self.act_redo.setEnabled(self.history.can_redo())

    def _refresh_after_history(self) -> None:
        self.view.scene.clearSelection()
        self.view.refresh()
        self.props.set_symbol(None)
        self.statusBar().showMessage("Lienzo actualizado")

    def undo(self) -> None:
        if self.history.undo():
            self._refresh_after_history()

    def redo(self) -> None:
        if self.history.redo():
            self._refresh_after_history()

    def clear_all(self) -> None:
        if not self.diagram.symbols and not self.diagram.wires:
            return
        ret = QMessageBox.question(
            self, "Limpiar todo",
            "¿Eliminar todos los símbolos y cables del esquema?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No)
        if ret != QMessageBox.StandardButton.Yes:
            return
        self.history.checkpoint()
        self.diagram.symbols.clear()
        self.diagram.wires.clear()
        self.history.commit()
        self._refresh_after_history()
        self.statusBar().showMessage("Esquema limpiado")

    # ------------------------------------------------------------------
    # Archivo
    # ------------------------------------------------------------------
    def _update_title(self) -> None:
        name = self.current_path or self.diagram.name
        self.setWindowTitle(f"{__appname__} - {os.path.basename(name)}")

    def new_document(self) -> None:
        if not self._confirm_discard():
            return
        self.diagram = Diagram()
        self.history.attach(self.diagram)
        self.view.diagram = self.diagram
        self.view.scene.diagram = self.diagram
        self.view.refresh()
        self.current_path = None
        self._update_title()
        self.statusBar().showMessage("Nuevo documento creado")

    def open_document(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Abrir esquema", "", "Esquemas (*.esq *.json);;Todos (*)")
        if not path:
            return
        try:
            self.diagram = Diagram.load_json(path)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo abrir el archivo:\n{e}")
            return
        self.current_path = path
        self.history.attach(self.diagram)
        self.view.diagram = self.diagram
        self.view.scene.diagram = self.diagram
        self.view.refresh()
        self._update_title()
        self.statusBar().showMessage(f"Abierto: {path}")

    def save_document(self) -> bool:
        if self.current_path:
            return self._save_to(self.current_path)
        return self.save_document_as()

    def save_document_as(self) -> bool:
        path, _ = QFileDialog.getSaveFileName(
            self, "Guardar esquema", "esquema.esq",
            "Esquemas (*.esq);;JSON (*.json)")
        if not path:
            return False
        if not path.endswith((".esq", ".json")):
            path += ".esq"
        self.current_path = path
        self._update_title()
        return self._save_to(path)

    def _save_to(self, path: str) -> bool:
        try:
            self.diagram.name = os.path.splitext(os.path.basename(path))[0]
            self.diagram.save_json(path)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo guardar:\n{e}")
            return False
        self.statusBar().showMessage(f"Guardado: {path}")
        return True

    def _confirm_discard(self) -> bool:
        return True

    # ------------------------------------------------------------------
    # Datos del proyecto (cajetín del plano)
    # ------------------------------------------------------------------
    def project_data(self) -> None:
        dlg = ProjectDialog(self, self.diagram.metadata)
        if dlg.exec():
            self.diagram.metadata.update(dlg.values())
            if not self.diagram.metadata.get("proyecto"):
                self.diagram.metadata["proyecto"] = self.diagram.name
            self.view.scene.update()
            self.statusBar().showMessage("Datos del proyecto actualizados")

    # ------------------------------------------------------------------
    # Exportación
    # ------------------------------------------------------------------
    def _render_painter(self, painter: QPainter):
        from ..core.renderer import DiagramRenderer
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        renderer = DiagramRenderer(painter, self.diagram, self.library)
        renderer.draw(show_grid=False, draw_pins=False)

    def export_png(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Exportar PNG", "esquema.png", "Imagen (*.png)")
        if not path:
            return
        from PySide6.QtGui import QImage
        from PySide6.QtCore import QRectF
        w, h = int(self.diagram.width), int(self.diagram.height)
        image = QImage(w, h, QImage.Format.Format_ARGB32)
        image.fill(QColor(self.diagram.background))
        painter = QPainter(image)
        self._render_painter(painter)
        painter.end()
        ok = image.save(path, "PNG")
        if ok:
            self.statusBar().showMessage(f"Exportado: {path}")
        else:
            QMessageBox.critical(self, "Error", "No se pudo exportar la imagen.")

    def export_pdf(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Exportar PDF", "esquema.pdf", "PDF (*.pdf)")
        if not path:
            return
        try:
            from ..core.pdf_export import export_pdf as _export_pdf
            ok = _export_pdf(self.diagram, self.library, path)
            if not ok:
                raise RuntimeError("No se pudo generar el PDF")
        except Exception as e:
            QMessageBox.warning(
                self, "PDF",
                "No se pudo exportar a PDF en esta plataforma "
                f"({type(e).__name__}). Puede usar Exportar PNG en su lugar.")
            return
        self.statusBar().showMessage(f"Exportado: {path}")

    def about(self) -> None:
        QMessageBox.about(
            self, "Acerca de Esquemático",
            f"<h2>{__appname__} v{__version__}</h2>"
            "<p>Generador visual de esquemas eléctricos de cuadros e "
            "instalaciones, unifilares y esquemáticos.</p>"
            "<p>Creado con Python y Qt (PySide6).</p>"
            "<p><b>Consejos:</b><br>"
            "- Doble clic en un símbolo lo rota 90°.<br>"
            "- Botón derecho para eliminar/duplicar/rotar.<br>"
            "- Rueda del ratón para hacer zoom.</p>")
