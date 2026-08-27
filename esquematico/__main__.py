"""Punto de entrada de la aplicación."""

from __future__ import annotations

import os
import sys


def resource_path(rel: str) -> str:
    """Devuelve la ruta al recurso, compatible con PyInstaller (--onefile)."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, rel)


def main() -> None:
    from PySide6.QtGui import QIcon
    from PySide6.QtWidgets import QApplication

    from esquematico.ui.main_window import MainWindow

    app = QApplication(sys.argv)
    app.setApplicationName("Esquemático")
    app.setOrganizationName("Esquemático")

    icon_path = resource_path(
        os.path.join("resources", "app.ico"))
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    win = MainWindow()
    win.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
