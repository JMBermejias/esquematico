"""Modelo de datos del diagrama eléctrico."""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Tuple


@dataclass
class SymbolInstance:
    """Instancia de un símbolo colocado en el lienzo."""

    symbol_id: str
    x: float
    y: float
    rotation: float = 0.0
    scale: float = 1.0
    color: str = "#2c3e50"
    label: str = ""
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SymbolInstance":
        return cls(
            symbol_id=data["symbol_id"],
            x=data.get("x", 0),
            y=data.get("y", 0),
            rotation=data.get("rotation", 0),
            scale=data.get("scale", 1.0),
            color=data.get("color", "#2c3e50"),
            label=data.get("label", ""),
            extra=data.get("extra") or {},
        )


@dataclass
class Wire:
    """Cable que conecta dos puntos del diagrama."""

    x1: float
    y1: float
    x2: float
    y2: float
    color: str = "#2c3e50"
    width: float = 2.0
    label: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Wire":
        return cls(
            x1=data.get("x1", 0),
            y1=data.get("y1", 0),
            x2=data.get("x2", 0),
            y2=data.get("y2", 0),
            color=data.get("color", "#2c3e50"),
            width=data.get("width", 2.0),
            label=data.get("label", ""),
        )


DEFAULT_METADATA: Dict[str, str] = {
    "proyecto": "",
    "cliente": "",
    "empresa": "",
    "autor": "",
    "fecha": "",
    "escala": "",
    "plano": "",
    "revision": "",
}


class Diagram:
    """Documento completo de esquema eléctrico."""

    def __init__(self) -> None:
        self.name: str = "Esquema sin título"
        self.symbols: List[SymbolInstance] = []
        self.wires: List[Wire] = []
        self.width: float = 1600.0
        self.height: float = 1000.0
        self.grid_size: float = 10.0
        self.background: str = "#ffffff"
        self.metadata: Dict[str, str] = dict(DEFAULT_METADATA)

    def add_symbol(self, symbol: SymbolInstance) -> None:
        self.symbols.append(symbol)

    def add_wire(self, wire: Wire) -> None:
        self.wires.append(wire)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "width": self.width,
            "height": self.height,
            "grid_size": self.grid_size,
            "background": self.background,
            "metadata": self.metadata,
            "symbols": [s.to_dict() for s in self.symbols],
            "wires": [w.to_dict() for w in self.wires],
        }

    def save_json(self, path: str) -> None:
        data = {
            "type": "esquematico",
            "version": 1,
            "diagram": self.to_dict(),
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @classmethod
    def load_json(cls, path: str) -> "Diagram":
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        diag_data = data.get("diagram", data)
        diagram = cls()
        diagram.name = diag_data.get("name", "Esquema sin título")
        diagram.width = diag_data.get("width", 1600.0)
        diagram.height = diag_data.get("height", 1000.0)
        diagram.grid_size = diag_data.get("grid_size", 10.0)
        diagram.background = diag_data.get("background", "#ffffff")
        meta = diag_data.get("metadata")
        diagram.metadata = {**DEFAULT_METADATA, **(meta or {})}
        diagram.symbols = [
            SymbolInstance.from_dict(s) for s in diag_data.get("symbols", [])
        ]
        diagram.wires = [Wire.from_dict(w) for w in diag_data.get("wires", [])]
        return diagram
