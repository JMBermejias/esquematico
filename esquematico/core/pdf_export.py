"""Exportación a PDF sin dependencias externas.

Genera un PDF válido en una sola página incrustando el esquema renderizado.
No depende del backend de impresión/PDF de Qt (QPdfWriter), que puede no
estar disponible según la plataforma o la versión de PySide6.
"""

from __future__ import annotations

import zlib
from typing import List


class _PDF:
    """Generador mínimo de un PDF de una página que dibuja una imagen RGB."""

    def __init__(self, width_pt: float, height_pt: float) -> None:
        self.width = width_pt
        self.height = height_pt
        self._objects: List[bytes] = []

    def add_object(self) -> int:
        self._objects.append(b"")
        return len(self._objects)

    def add_stream(self, data: bytes, extra: bytes = b"") -> int:
        num = self.add_object()
        compressed = zlib.compress(data)
        head = (
            b"<< /Length " + str(len(compressed)).encode() + b" "
            + extra + b" >>\nstream\n"
        )
        self._objects[num - 1] = head + compressed + b"\nendstream"
        return num

    def embed_rgb_image(self, rgb_bytes: bytes, w: int, h: int) -> int:
        num = self.add_object()
        compressed = zlib.compress(rgb_bytes)
        head = (
            b"<< /Type /XObject /Subtype /Image "
            + f"/Width {w} /Height {h} ".encode()
            + b"/ColorSpace /DeviceRGB /BitsPerComponent 8 "
            + f"/Length {len(compressed)} ".encode()
            + b"/Filter /FlateDecode >>\nstream\n"
        )
        self._objects[num - 1] = head + compressed + b"\nendstream"
        return num

    def build(self, image_data: bytes, w: int, h: int) -> bytes:
        img_num = self.embed_rgb_image(image_data, w, h)

        # La página dibuja la imagen ocupando todo el MediaBox.
        content = (
            b"q\n"
            + f"{self.width:.2f} 0 0 {self.height:.2f} 0 0 cm\n".encode()
            + f"/Im{img_num} Do\n".encode()
            + b"Q\n"
        )
        content_num = self.add_stream(content)

        page_num = self.add_object()
        self._objects[page_num - 1] = (
            b"<< /Type /Page /Parent 1 0 R "
            + f"/MediaBox [0 0 {self.width:.2f} {self.height:.2f}] ".encode()
            + b"/Resources << /XObject << "
            + f"/Im{img_num} {img_num} 0 R".encode() + b" >> >> "
            + f"/Contents {content_num} 0 R >>".encode()
        )

        pages_num = self.add_object()
        self._objects[pages_num - 1] = (
            b"<< /Type /Pages /Kids [" + str(page_num).encode()
            + b" 0 R] /Count 1 >>"
        )

        catalog_num = self.add_object()
        self._objects[catalog_num - 1] = (
            b"<< /Type /Catalog /Pages " + str(pages_num).encode() + b" 0 R >>"
        )

        return self._assemble(catalog_num)

    def _assemble(self, catalog_num: int) -> bytes:
        out = bytearray(b"%PDF-1.4\n")
        n = len(self._objects)
        offsets = []
        for i, obj in enumerate(self._objects, start=1):
            offsets.append(len(out))
            out += f"{i} 0 obj\n".encode()
            if obj == b"":
                out += b"<< >>\n"
            else:
                out += obj + b"\n"
            out += b"endobj\n"
        xref = len(out)
        out += f"xref\n0 {n + 1}\n".encode()
        out += b"0000000000 65535 f \n"
        for off in offsets:
            out += f"{off:010d} 00000 n \n".encode()
        out += (f"trailer\n<< /Size {n + 1} /Root "
                f"{catalog_num} 0 R >>\n").encode()
        out += b"startxref\n" + str(xref).encode() + b"\n%%EOF\n"
        return bytes(out)


def _pixel_bytes(image) -> bytes:
    """Devuelve los bytes RGB (arriba->abajo) de una QImage."""
    from PySide6.QtCore import QBuffer, QByteArray
    from PySide6.QtGui import QColorSpace, QImage

    image = image.convertToFormat(QImage.Format.Format_RGB888)
    w = image.width()
    h = image.height()
    step = image.bytesPerLine()
    ba = image.constBits()
    count = step * h
    buf = ba[:count]
    rows = []
    for y in range(h):
        start = y * step
        rows.append(bytes(buf[start:start + w * 3]))
    rows.reverse()  # PDF espera bottom-up
    return b"".join(rows)


def render_to_rgb(diagram, library, width_px: int, height_px: int
                  ) -> "object":
    """Renderiza el diagrama y devuelve la QImage RGB."""
    from PySide6.QtGui import QColor, QImage, QPainter

    from .renderer import DiagramRenderer

    image = QImage(width_px, height_px, QImage.Format.Format_ARGB32)
    image.fill(QColor(diagram.background))
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    renderer = DiagramRenderer(painter, diagram, library)
    renderer.draw(show_grid=False, draw_pins=False)
    painter.end()
    return image.convertToFormat(QImage.Format.Format_RGB888)


def export_pdf(diagram, library, path: str) -> bool:
    """Exporta el diagrama a un PDF de una sola página (contiene el esquema
    como imagen). Devuelve True si se generó correctamente."""
    w_px = int(diagram.width)
    h_px = int(diagram.height)

    image = render_to_rgb(diagram, library, w_px, h_px)
    rgb = _pixel_bytes(image)

    dpi = 96.0
    width_pt = w_px * 72.0 / dpi
    height_pt = h_px * 72.0 / dpi

    pdf = _PDF(width_pt, height_pt).build(rgb, w_px, h_px)
    with open(path, "wb") as f:
        f.write(pdf)
    return True
