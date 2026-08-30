"""Biblioteca de símbolos eléctricos.

Cada símbolo se describe mediante primitivas de dibujo (líneas, círculos,
rectángulos, arcos, texto/trazos) en un espacio de coordenadas local
normalizado. La tercera parte del dibujo primitivo permite indicar si el
elemento es un punto de conexión (pin) sobre el que se pueden enganchar
cables.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple


@dataclass
class Primitive:
    kind: str  # line | circle | rect | arc | text | pin
    args: List[float]
    style: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Symbol:
    id: str
    name: str
    category: str
    primitives: List[Primitive]
    width: float
    height: float
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "width": self.width,
            "height": self.height,
            "description": self.description,
            "primitives": [
                {"kind": p.kind, "args": p.args, "style": p.style}
                for p in self.primitives
            ],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Symbol":
        prims = [
            Primitive(
                kind=p["kind"],
                args=p.get("args", []),
                style=p.get("style", {}),
            )
            for p in data.get("primitives", [])
        ]
        return cls(
            id=data["id"],
            name=data.get("name", data["id"]),
            category=data.get("category", "Otros"),
            width=data.get("width", 100),
            height=data.get("height", 100),
            description=data.get("description", ""),
            primitives=prims,
        )


def _L(*args, **kw) -> Primitive:
    return Primitive("line", list(args), kw)


def _C(*args, **kw) -> Primitive:
    return Primitive("circle", list(args), kw)


def _R(*args, **kw) -> Primitive:
    return Primitive("rect", list(args), kw)


def _A(*args, **kw) -> Primitive:
    return Primitive("arc", list(args), kw)


def _T(*args, **kw) -> Primitive:
    return Primitive("text", list(args), kw)


def _P(x, y, **kw) -> Primitive:
    return Primitive("pin", [x, y], kw)


def _force_breaks(func) -> None:
    pass


def build_library() -> List[Symbol]:
    """Devuelve la biblioteca completa de símbolos eléctricos."""

    # Nota: coordenadas normalizadas; cada símbolo tiene su propio tamaño.

    symbols = []

    # ---------- Protección (cuadros / unifilar) ----------
    symbols.append(Symbol(
        id="breaker_1p",
        name="Interruptor magnetotérmico 1P",
        category="Protección",
        width=36, height=80,
        description="Disyuntor / magnetotérmico unipolar",
        primitives=[
            _L(-8, -40, -8, 40),
            _L(8, -40, 8, 40),
            _L(-8, -18, 8, -18),
            _L(-8, 18, 8, 18),
            _L(-8, -18, -8, 18),
            _L(-8, 18, -8, 40),
            _L(8, 18, 8, 40),
            _L(-8, -18, -8, -40),
            _P(0, -45), _P(0, 45),
        ],
    ))

    symbols.append(Symbol(
        id="breaker_2p",
        name="Interruptor magnetotérmico 2P",
        category="Protección",
        width=76, height=80,
        description="Disyuntor bipolar",
        primitives=[
            _L(-18, -40, -18, 40, color="#2c3e50"),
            _L(18, -40, 18, 40, color="#2c3e50"),
            _L(-18, -18, 18, -18),
            _L(-18, 18, 18, 18),
            _L(-18, 18, -18, 40),
            _L(-18, -18, -18, -40),
            _L(18, 18, 18, 40),
            _L(18, -18, 18, -40),
            _L(18, -18, 18, -40),
            _P(-18, -45), _P(-18, 45),
            _P(18, -45), _P(18, 45),
        ],
    ))

    symbols.append(Symbol(
        id="breaker_3p",
        name="Interruptor magnetotérmico 3P",
        category="Protección",
        width=56, height=100,
        description="Disyuntor tripolar",
        primitives=[
            _L(-22, -50, -22, 50),
            _L(0, -50, 0, 50),
            _L(22, -50, 22, 50),
            _L(-22, -22, 22, -22),
            _L(-22, 22, 22, 22),
            _L(-22, -38, 22, -38),
            _L(-22, 38, 22, 38),
            _P(-22, -55), _P(-22, 55),
            _P(0, -55), _P(0, 55),
            _P(22, -55), _P(22, 55),
        ],
    ))

    symbols.append(Symbol(
        id="diff_switch",
        name="Interruptor diferencial",
        category="Protección",
        width=44, height=100,
        description="Diferencial (protección contra fugas)",
        primitives=[
            _L(-8, -45, -8, 45),
            _L(8, -45, 8, 45),
            _L(-8, 45, 8, -45),
            _L(-14, -30, 0, -20),
            _L(-8, -16, 8, -30),
            _L(-22, -35, 22, 22),
            _L(-22, 30, -22, -35),
            _L(22, -35, 22, 30),
            _L(-22, 30, 22, 30),
            _P(0, -50), _P(0, 50),
        ],
    ))

    symbols.append(Symbol(
        id="fuse",
        name="Fusible",
        category="Protección",
        width=58, height=50,
        description="Fusible en serie",
        primitives=[
            _L(-25, 0, 0, 0),
            _R(0, -20, 26, 40),
            _L(26, 0, 25, 0),
        ],
    ))

    symbols.append(Symbol(
        id="contactor",
        name="Contactor / relé",
        category="Protección",
        width=50, height=90,
        description="Contactor trifásico",
        primitives=[
            _L(-12, -40, -12, 40),
            _L(12, -40, 12, 40),
            _L(-12, -40, 12, 40),
            _L(0, 40, 0, 30),
            _L(-12, 0, 12, 0),
            _L(-12, 0, 12, 0),
            _L(-20, 40, -12, 40),
            _P(-12, -45), _P(-12, 45),
            _P(12, -45), _P(12, 45),
        ],
    ))

    # ---------- Interruptores / conmutadores ----------
    symbols.append(Symbol(
        id="switch_no",
        name="Interruptor NA (normalmente abierto)",
        category="Interruptores",
        width=46, height=40,
        description="Contacto normalmente abierto",
        primitives=[
            _L(-20, 0, 0, 18),
            _L(0, 18, 20, 18),
            _P(-20, 0), _P(20, 18),
        ],
    ))

    symbols.append(Symbol(
        id="switch_nc",
        name="Contacto NC (normalmente cerrado)",
        category="Interruptores",
        width=46, height=40,
        description="Contacto normalmente cerrado",
        primitives=[
            _L(-20, 0, 0, 18),
            _L(0, 18, 20, 18),
            _L(0, 18, 20, 0),
            _P(-20, 0), _P(20, 0),
        ],
    ))

    symbols.append(Symbol(
        id="switch_spst",
        name="Interruptor simple (SPST)",
        category="Interruptores",
        width=46, height=40,
        description="Interruptor unipolar",
        primitives=[
            _L(-20, 0, 0, -18),
            _L(0, -18, 20, 0),
            _P(-20, 0), _P(20, 0),
        ],
    ))

    symbols.append(Symbol(
        id="pushbutton_no",
        name="Pulsador NA",
        category="Interruptores",
        width=46, height=44,
        description="Pulsador normalmente abierto",
        primitives=[
            _L(-20, 0, 0, 18),
            _L(0, 18, 20, 18),
            _L(0, 30, 20, 30),
            _L(0, 30, 0, 0),
            _P(-20, 0), _P(20, 18),
        ],
    ))

    symbols.append(Symbol(
        id="thermal_relay",
        name="Relé térmico",
        category="Protección",
        width=16, height=90,
        description="Relé térmico de protección de motor",
        primitives=[
            _L(0, -40, 0, -10),
            _L(-8, -10, 8, -10),
            _L(0, -10, 0, 10),
            _L(-8, 10, 8, 10),
            _L(0, 10, 0, 40),
            _L(-8, -40, 8, -40),
            _L(-8, 40, 8, 40),
            _L(8, -40, 8, -10),
            _L(8, 10, 8, 40),
            _L(-8, -40, -8, -10),
            _L(-8, 10, -8, 40),
            _P(0, -45), _P(0, 45),
        ],
    ))

    # ---------- Receptores / cargas ----------
    symbols.append(Symbol(
        id="motor_3p",
        name="Motor trifásico (M)",
        category="Receptores",
        width=78, height=78,
        description="Motor trifásico",
        primitives=[
            _C(0, 0, 36),
            _L(-32, -14, 26, -26),
            _L(32, -16, -26, 26),
            _T(-12, -8, "M"),
            _L(-45, -10, -45, -45),
            _L(45, -10, 45, -45),
            _L(45, -10, 45, -45),
            _L(-45, -45, 45, -45),
            _L(-45, -10, 45, -10),
            _P(-45, 20), _P(0, 20), _P(45, 20),
            _P(-45, -50), _P(0, -50), _P(45, -50),
        ],
    ))

    symbols.append(Symbol(
        id="lamp",
        name="Lámpara / lámpara de señalización",
        category="Receptores",
        width=48, height=48,
        description="Lámpara incandescente o de señalización",
        primitives=[
            _C(0, 0, 22),
            _L(0, -14, 0, 14),
            _L(-14, 0, 14, 0),
            _L(0, 0, 0, 0),
            _L(-18, 0, -22, 0),
            _L(18, 0, 22, 0),
            _L(0, 22, 0, 26),
            _L(0, -22, 0, -26),
            _P(0, -26), _P(0, 26),
        ],
    ))

    symbols.append(Symbol(
        id="lamp_x",
        name="Lámpara de incandescencia (X)",
        category="Receptores",
        width=48, height=48,
        description="Lámpara de incandescencia",
        primitives=[
            _C(0, 0, 22),
            _L(-14, -14, 14, 14),
            _L(-14, 14, 14, -14),
            _L(0, 22, 0, 26),
            _L(0, -22, 0, -26),
            _P(0, -26), _P(0, 26),
        ],
    ))

    symbols.append(Symbol(
        id="socket",
        name="Base de enchufe / tomacorriente",
        category="Receptores",
        width=50, height=40,
        description="Base de toma de corriente",
        primitives=[
            _L(-10, -6, -10, 20),
            _L(10, -6, 10, 20),
            _L(-10, -6, -22, -6),
            _L(10, -6, 22, -6),
            _P(-22, -6), _P(22, -6),
        ],
    ))

    symbols.append(Symbol(
        id="resistor",
        name="Resistencia",
        category="Receptores",
        width=50, height=36,
        description="Resistencia (representación zigzag)",
        primitives=[
            _L(-22, 0, 0, -14),
            _L(0, -14, 12, 14),
            _L(12, 14, 22, 0),
            _L(-22, 0, -25, 0),
            _L(22, 0, 25, 0),
            _P(-25, 0), _P(25, 0),
        ],
    ))

    symbols.append(Symbol(
        id="capacitor",
        name="Condensador",
        category="Receptores",
        width=36, height=36,
        description="Condensador / capacitor",
        primitives=[
            _L(-22, 0, -2, 0),
            _L(2, 0, 22, 0),
            _L(0, -7, 0, 7),
            _L(2, -7, 2, 7),
            _L(2, -7, 2, 7),
            _P(-22, 0), _P(22, 0),
        ],
    ))

    symbols.append(Symbol(
        id="transformer",
        name="Transformador / fuente",
        category="Receptores",
        width=60, height=56,
        description="Transformador monofásico",
        primitives=[
            _L(-20, -22, 20, -22),
            _L(-24, -26, 24, -26),
            _L(-20, -22, -24, -26),
            _L(20, -22, 24, -26),
            _L(-20, 22, 20, 22),
            _L(-24, 26, 24, 26),
            _L(-20, 22, -24, 26),
            _L(20, 22, 24, 26),
            _L(0, -26, 0, -34),
            _L(0, 26, 0, 34),
            _P(0, -34), _P(0, 34),
        ],
    ))

    # ---------- Tierra / alimentación ----------
    symbols.append(Symbol(
        id="ground",
        name="Toma de tierra",
        category="Tierra y alimentación",
        width=46, height=36,
        description="Conexión a tierra",
        primitives=[
            _L(0, -18, 0, -8),
            _L(0, -8, -18, 0),
            _L(-18, 0, 18, 0),
            _L(-12, 4, 12, 4),
            _L(-6, 8, 6, 8),
            _P(0, -18),
        ],
    ))

    symbols.append(Symbol(
        id="supply_1p",
        name="Red monofásica (L, N)",
        category="Tierra y alimentación",
        width=46, height=40,
        description="Alimentación monofásica",
        primitives=[
            _L(-6, -20, -6, -8),
            _L(6, -20, 6, -8),
            _L(-6, -8, 6, -8),
            _L(-6, -8, -6, 0),
            _L(6, -8, 6, 0),
            _L(0, 0, 0, 0),
            _P(-6, 0), _P(6, 0),
        ],
    ))

    symbols.append(Symbol(
        id="supply_3p",
        name="Red trifásica 3L+N",
        category="Tierra y alimentación",
        width=50, height=36,
        description="Alimentación trifásica",
        primitives=[
            _L(-18, -18, -18, -8),
            _L(0, -18, 0, -8),
            _L(18, -18, 18, -8),
            _L(-18, -8, 18, -8),
            _L(-18, -8, -18, 0),
            _L(0, -8, 0, 0),
            _L(18, -8, 18, 0),
            _P(-18, 0), _P(0, 0), _P(18, 0),
        ],
    ))

    symbols.append(Symbol(
        id="battery",
        name="Batería / fuente CC",
        category="Tierra y alimentación",
        width=40, height=44,
        description="Batería o pila",
        primitives=[
            _L(-8, -16, -8, -6),
            _L(8, -16, 8, -6),
            _L(-8, -16, 8, -16),
            _L(8, -6, 8, 6),
            _L(8, 6, 8, 16),
            _L(-8, 6, -8, 16),
            _L(-8, 16, 8, 16),
            _L(-8, 6, 8, 6),
            _P(0, -20), _P(0, 20),
        ],
    ))

    # ---------- Lógica / control ----------
    symbols.append(Symbol(
        id="coil",
        name="Bobina de relé / contactor",
        category="Lógica y control",
        width=46, height=52,
        description="Bobina",
        primitives=[
            _L(-8, 0, 8, 0),
            _L(-20, 0, 20, 0),
            _L(8, -8, 8, 8),
            _L(-20, -20, 20, 20),
            _L(-20, 20, 20, -20),
            _L(-22, 0, -28, 0),
            _L(22, 0, 28, 0),
            _P(-28, 0), _P(28, 0),
        ],
    ))

    symbols.append(Symbol(
        id="timer",
        name="Temporizador / relé de tiempo",
        category="Lógica y control",
        width=56, height=56,
        description="Temporizador",
        primitives=[
            _R(0, 0, 40, 40),
            _L(20, 4, 20, 12),
            _T(22, 16, "t"),
            _T(6, 16, "T"),
            _L(-6, 20, 0, 20),
            _L(40, 20, 46, 20),
            _P(-6, 20), _P(46, 20),
        ],
    ))

    # ---------- Instalación / cuadro ----------
    symbols.append(Symbol(
        id="panel",
        name="Cuadro eléctrico",
        category="Instalación",
        width=90, height=120,
        description="Cuadro general / caja de distribución",
        primitives=[
            _R(0, 0, 90, 120, rounded=True),
            _L(6, 8, 6, 34),
            _L(30, 8, 30, 34),
            _R(14, 20, 40, 60, style="panel"),
            _L(12, 12, 78, 12),
            _L(12, 12, 12, 40),
            _L(78, 12, 78, 40),
            _L(6, 40, 50, 40),
            _L(50, 40, 50, 90),
            _L(6, 90, 50, 90),
            _L(50, 40, 84, 40),
            _L(78, 40, 78, 90),
            _L(60, 105, 60, 118),
            _P(45, 118),
        ],
    ))

    symbols.append(Symbol(
        id="label",
        name="Etiqueta / texto",
        category="Instalación",
        width=80, height=30,
        description="Texto libre",
        primitives=[
            _T(0, 10, "Texto"),
        ],
    ))

    symbols.append(Symbol(
        id="junction",
        name="Nudo / empalme",
        category="Instalación",
        width=14, height=14,
        description="Nodo de conexión",
        primitives=[
            _C(0, 0, 7, filled=True),
        ],
    ))

    # ---------- Electrónica ----------
    symbols.append(Symbol(
        id="diode",
        name="Diodo",
        category="Electrónica",
        width=50, height=28,
        description="Diodo semiconductor (ánodo-cátodo)",
        primitives=[
            _L(-25, 0, -10, 0),
            _L(-10, 0, 10, -13),
            _L(-10, 0, 10, 13),
            _L(10, -13, 10, 13),
            _L(10, 0, 25, 0),
            _P(-25, 0), _P(25, 0),
        ],
    ))

    symbols.append(Symbol(
        id="led",
        name="LED",
        category="Electrónica",
        width=54, height=40,
        description="Diodo emisor de luz",
        primitives=[
            _L(-25, 0, -10, 0),
            _L(-10, 0, 10, -13),
            _L(-10, 0, 10, 13),
            _L(10, -13, 10, 13),
            _L(10, 0, 25, 0),
            _L(12, 0, 24, -11),
            _L(19, -16, 24, -11),
            _L(24, -11, 24, -17),
            _L(12, 0, 24, 11),
            _L(19, 16, 24, 11),
            _L(24, 11, 24, 17),
            _P(-25, 0), _P(25, 0),
        ],
    ))

    symbols.append(Symbol(
        id="zener",
        name="Diodo Zener",
        category="Electrónica",
        width=50, height=28,
        description="Diodo Zener (regulación de tensión)",
        primitives=[
            _L(-25, 0, -10, 0),
            _L(-10, 0, 10, -13),
            _L(-10, 0, 10, 13),
            _L(10, -13, 10, 13),
            _L(10, 13, 17, 6),
            _L(10, 0, 25, 0),
            _P(-25, 0), _P(25, 0),
        ],
    ))

    symbols.append(Symbol(
        id="photodiode",
        name="Fotodiodo",
        category="Electrónica",
        width=58, height=40,
        description="Diodo sensible a la luz",
        primitives=[
            _L(-25, 0, -10, 0),
            _L(-10, 0, 10, -13),
            _L(-10, 0, 10, 13),
            _L(10, -13, 10, 13),
            _L(10, 0, 25, 0),
            _L(-42, -12, -34, -20),
            _L(-38, -22, -34, -20),
            _L(-34, -20, -34, -14),
            _L(-42, 12, -34, 20),
            _L(-38, 22, -34, 20),
            _L(-34, 20, -34, 14),
            _P(-25, 0), _P(25, 0),
        ],
    ))

    symbols.append(Symbol(
        id="transistor_npn",
        name="Transistor NPN",
        category="Electrónica",
        width=52, height=40,
        description="Transistor bipolar NPN",
        primitives=[
            _L(-26, 0, -12, 0),
            _L(-12, -16, -12, 16),
            _L(-12, -16, 22, -16),
            _L(-12, 16, 22, 16),
            _L(22, 16, 17, 10),
            _L(22, 16, 17, 22),
            _P(-26, 0), _P(22, -16), _P(22, 16),
        ],
    ))

    symbols.append(Symbol(
        id="transistor_pnp",
        name="Transistor PNP",
        category="Electrónica",
        width=52, height=40,
        description="Transistor bipolar PNP",
        primitives=[
            _L(-26, 0, -12, 0),
            _L(-12, -16, -12, 16),
            _L(-12, -16, 22, -16),
            _L(-12, 16, 22, 16),
            _L(-12, 16, -7, 10),
            _L(-12, 16, -7, 22),
            _P(-26, 0), _P(22, -16), _P(22, 16),
        ],
    ))

    symbols.append(Symbol(
        id="scr",
        name="Tiristor (SCR)",
        category="Electrónica",
        width=50, height=40,
        description="Rectificador controlado de silicio",
        primitives=[
            _L(-25, 0, -10, 0),
            _L(-10, 0, 10, -12),
            _L(-10, 0, 10, 12),
            _L(10, -12, 10, 12),
            _L(10, 0, 25, 0),
            _L(10, 8, 18, 16),
            _P(-25, 0), _P(25, 0), _P(18, 16),
        ],
    ))

    symbols.append(Symbol(
        id="opamp",
        name="Amplificador operacional",
        category="Electrónica",
        width=56, height=30,
        description="Operacional (op-amp): entrada 2, salida 1",
        primitives=[
            _L(-8, 0, 20, -14),
            _L(20, -14, 20, 14),
            _L(20, 14, -8, 0),
            _L(-18, -8, -8, -8),
            _L(-18, 8, -8, 8),
            _L(20, 0, 28, 0),
            _T(-4, -11, "-"),
            _T(-4, 9, "+"),
            _P(-18, -8), _P(-18, 8), _P(28, 0),
        ],
    ))

    symbols.append(Symbol(
        id="inductor",
        name="Bobina / inductor",
        category="Electrónica",
        width=48, height=14,
        description="Inductor o bobina",
        primitives=[
            _L(-24, 0, -18, 0),
            _L(-18, 0, -15, -5.2),
            _L(-15, -5.2, -12, -6),
            _L(-12, -6, -9, -5.2),
            _L(-9, -5.2, -6, 0),
            _L(-6, 0, -3, -5.2),
            _L(-3, -5.2, 0, -6),
            _L(0, -6, 3, -5.2),
            _L(3, -5.2, 6, 0),
            _L(6, 0, 9, -5.2),
            _L(9, -5.2, 12, -6),
            _L(12, -6, 15, -5.2),
            _L(15, -5.2, 18, 0),
            _L(18, 0, 24, 0),
            _P(-24, 0), _P(24, 0),
        ],
    ))

    symbols.append(Symbol(
        id="potentiometer",
        name="Potenciómetro",
        category="Electrónica",
        width=50, height=40,
        description="Resistencia variable con cursor",
        primitives=[
            _L(-22, 0, -11, -12),
            _L(-11, -12, 0, 12),
            _L(0, 12, 11, -12),
            _L(11, -12, 22, 0),
            _L(-25, 0, -22, 0),
            _L(22, 0, 25, 0),
            _L(0, -2, 0, 16),
            _L(0, 16, -5, 22),
            _L(0, 16, 5, 22),
            _P(-25, 0), _P(25, 0),
        ],
    ))

    symbols.append(Symbol(
        id="crystal",
        name="Oscilador de cuarzo",
        category="Electrónica",
        width=48, height=18,
        description="Cristal / cuarzo",
        primitives=[
            _L(-24, 0, -16, 0),
            _L(16, 0, 24, 0),
            _R(-16, -8, 32, 16),
            _L(-2, -8, -2, 8),
            _L(2, -8, 2, 8),
            _P(-24, 0), _P(24, 0),
        ],
    ))

    symbols.append(Symbol(
        id="ic_chip",
        name="Circuito integrado (CI)",
        category="Electrónica",
        width=48, height=36,
        description="Chip / circuito integrado de pines",
        primitives=[
            _R(-18, -12, 36, 24),
            _L(-18, -6, -24, -6),
            _L(-18, 6, -24, 6),
            _L(18, -6, 24, -6),
            _L(18, 6, 24, 6),
            _L(0, -12, 0, -18),
            _L(0, 12, 0, 18),
            _P(-24, -6), _P(-24, 6),
            _P(24, -6), _P(24, 6),
            _P(0, -18), _P(0, 18),
        ],
    ))

    # ---------- Fotovoltaica (energía solar) ----------
    symbols.append(Symbol(
        id="panel_solar",
        name="Módulo / panel fotovoltaico",
        category="Fotovoltaica",
        width=56, height=44,
        description="Panel o módulo fotovoltaico captador de irradiación",
        primitives=[
            _R(-28, -22, 56, 44),
            _L(-16, -14, -6, 14),
            _L(0, -14, 10, 14),
            _L(16, -14, 26, 14),
            _L(-4, -38, -4, -26),
            _L(-4, -28, -8, -33),
            _L(-4, -28, 0, -33),
            _L(20, -38, 20, -26),
            _L(20, -28, 16, -33),
            _L(20, -28, 24, -33),
            _P(0, -22), _P(0, 22),
        ],
    ))

    symbols.append(Symbol(
        id="inversor_pv",
        name="Inversor fotovoltaico",
        category="Fotovoltaica",
        width=68, height=36,
        description="Inversor DC/AC de una instalación fotovoltaica",
        primitives=[
            _R(-28, -18, 56, 36),
            _L(-22, -6, -22, 6),
            _L(-16, -6, -16, 6),
            _L(10, -8, 14, -3),
            _L(14, -3, 10, 2),
            _L(10, 2, 14, 7),
            _L(-28, 0, -34, 0), _P(-34, 0),
            _L(28, 0, 34, 0), _P(34, 0),
        ],
    ))

    symbols.append(Symbol(
        id="regulador_carga",
        name="Regulador de carga",
        category="Fotovoltaica",
        width=68, height=36,
        description="Regulador de carga de baterías (M.P.P.T.)",
        primitives=[
            _R(-28, -18, 56, 36),
            _T(-6, 5, "REG"),
            _L(-28, 0, -34, 0), _P(-34, 0),
            _L(28, 0, 34, 0), _P(34, 0),
        ],
    ))

    symbols.append(Symbol(
        id="caja_combinacion",
        name="Caja de combinación (PV)",
        category="Fotovoltaica",
        width=60, height=44,
        description="Caja de combinación / fuse box de la instalación solar",
        primitives=[
            _R(-24, -22, 48, 44),
            _L(-24, -10, -30, -10), _P(-30, -10),
            _L(-24, 0, -30, 0), _P(-30, 0),
            _L(-24, 10, -30, 10), _P(-30, 10),
            _L(24, 0, 30, 0), _P(30, 0),
        ],
    ))

    symbols.append(Symbol(
        id="sol_irradiacion",
        name="Sol / irradiación",
        category="Fotovoltaica",
        width=52, height=52,
        description="Fuente de irradiación solar",
        primitives=[
            _C(0, 0, 14),
            _L(0, -18, 0, -26),
            _L(0, 18, 0, 26),
            _L(-18, 0, -26, 0),
            _L(18, 0, 26, 0),
            _L(-13, -13, -18, -18),
            _L(13, 13, 18, 18),
            _L(-13, 13, -18, 18),
            _L(13, -13, 18, -18),
        ],
    ))

    symbols.append(Symbol(
        id="bateria_fv",
        name="Batería de acumulación solar",
        category="Fotovoltaica",
        width=40, height=44,
        description="Batería de acumulación para sistema fotovoltaico",
        primitives=[
            _L(-10, -16, -10, -6),
            _L(10, -16, 10, -6),
            _L(-10, -16, 10, -16),
            _L(10, -6, 10, 6),
            _L(10, 6, 10, 16),
            _L(-10, 6, -10, 16),
            _L(-10, 16, 10, 16),
            _L(-10, 6, 10, 6),
            _P(0, -20), _P(0, 20),
        ],
    ))

    # ---------- Hidráulica ----------
    symbols.append(Symbol(
        id="bomba_hidra",
        name="Bomba hidráulica",
        category="Hidráulica",
        width=52, height=36,
        description="Bomba hidráulica de desplazamiento positivo",
        primitives=[
            _C(0, 0, 18),
            _L(2, -10, 2, 10),
            _L(2, -10, 16, 0),
            _L(2, 10, 16, 0),
            _L(-18, 0, -26, 0), _P(-26, 0),
            _L(18, 0, 26, 0), _P(26, 0),
        ],
    ))

    symbols.append(Symbol(
        id="motor_hidra",
        name="Motor hidráulico",
        category="Hidráulica",
        width=52, height=52,
        description="Motor hidráulico",
        primitives=[
            _C(0, 0, 18),
            _L(-16, -10, -16, 10),
            _L(-16, -10, -2, 0),
            _L(-16, 10, -2, 0),
            _L(0, -18, 0, -26), _P(0, -26),
            _L(0, 18, 0, 26), _P(0, 26),
        ],
    ))

    symbols.append(Symbol(
        id="cilindro_hidra",
        name="Cilindro hidráulico (doble efecto)",
        category="Hidráulica",
        width=48, height=44,
        description="Cilindro hidráulico de doble efecto",
        primitives=[
            _L(-24, 0, -6, 0),
            _R(-6, -14, 18, 28),
            _L(-4, -14, -4, -22), _P(-4, -22),
            _L(-4, 14, -4, 22), _P(-4, 22),
            _P(-24, 0),
        ],
    ))

    symbols.append(Symbol(
        id="valvula_hidra",
        name="Válvula direccional hidráulica",
        category="Hidráulica",
        width=64, height=32,
        description="Válvula direccional de 4 vías",
        primitives=[
            _R(-26, -16, 16, 32),
            _R(10, -16, 16, 32),
            _L(-18, 8, -2, -8),
            _L(18, 8, 2, -8),
            _L(-26, 8, -32, 8), _P(-32, 8),
            _L(-26, -8, -32, -8), _P(-32, -8),
            _L(26, 8, 32, 8), _P(32, 8),
            _L(26, -8, 32, -8), _P(32, -8),
        ],
    ))

    symbols.append(Symbol(
        id="antirretorno_hidra",
        name="Válvula antirretorno",
        category="Hidráulica",
        width=48, height=20,
        description="Válvula antirretorno (check valve)",
        primitives=[
            _L(-24, 0, -8, 0),
            _L(-8, 0, 6, -10), _L(-8, 0, 6, 10), _L(6, -10, 6, 10),
            _L(6, 0, 10, -3),
            _L(10, -3, 14, 3),
            _L(14, 3, 18, -3),
            _L(18, -3, 22, 0),
            _L(22, 0, 24, 0),
            _P(-24, 0), _P(24, 0),
        ],
    ))

    symbols.append(Symbol(
        id="deposito_hidra",
        name="Depósito / tanque hidráulico",
        category="Hidráulica",
        width=32, height=28,
        description="Depósito o tanque de aceite hidráulico",
        primitives=[
            _R(-16, -14, 32, 18),
            _L(-16, -4, 16, -4),
            _L(0, 4, 0, 12), _P(0, 12),
        ],
    ))

    symbols.append(Symbol(
        id="filtro_hidra",
        name="Filtro hidráulico",
        category="Hidráulica",
        width=36, height=28,
        description="Filtro de línea hidráulica",
        primitives=[
            _R(-12, -14, 24, 28),
            _L(-8, -8, 8, 8),
            _L(-8, 8, 8, -8),
            _L(-18, 0, -12, 0), _P(-18, 0),
            _L(12, 0, 18, 0), _P(18, 0),
        ],
    ))

    symbols.append(Symbol(
        id="acumulador_hidra",
        name="Acumulador hidráulico",
        category="Hidráulica",
        width=32, height=36,
        description="Acumulador hidráulico de membrana",
        primitives=[
            _C(0, 0, 14),
            _L(-14, 0, 14, 0),
            _L(0, 14, 0, 22), _P(0, 22),
        ],
    ))

    symbols.append(Symbol(
        id="manometro_hidra",
        name="Manómetro hidráulico",
        category="Hidráulica",
        width=28, height=34,
        description="Manómetro de presión de aceite",
        primitives=[
            _C(0, -2, 13),
            _L(0, -2, 8, -9),
            _L(0, -15, 0, -22), _P(0, -22),
        ],
    ))

    # ---------- Neumática ----------
    symbols.append(Symbol(
        id="compresor",
        name="Compresor de aire",
        category="Neumática",
        width=52, height=52,
        description="Compresor de aire comprimido",
        primitives=[
            _C(0, 0, 18),
            _L(2, -10, 2, 10),
            _L(2, -10, 16, 0),
            _L(2, 10, 16, 0),
            _L(0, -18, 0, -26), _P(0, -26),
            _L(18, 0, 26, 0), _P(26, 0),
        ],
    ))

    symbols.append(Symbol(
        id="motor_neum",
        name="Motor neumático",
        category="Neumática",
        width=52, height=36,
        description="Motor de aire comprimido",
        primitives=[
            _C(0, 0, 18),
            _L(-16, -10, -16, 10),
            _L(-16, -10, -2, 0),
            _L(-16, 10, -2, 0),
            _L(-26, 0, -18, 0), _P(-26, 0),
            _L(18, 0, 26, 0), _P(26, 0),
        ],
    ))

    symbols.append(Symbol(
        id="cilindro_neum",
        name="Cilindro neumático (doble efecto)",
        category="Neumática",
        width=48, height=44,
        description="Cilindro neumático de doble efecto",
        primitives=[
            _L(-24, 0, -6, 0),
            _R(-6, -14, 18, 28),
            _L(-4, -14, -4, -22), _P(-4, -22),
            _L(-4, 14, -4, 22), _P(-4, 22),
            _P(-24, 0),
        ],
    ))

    symbols.append(Symbol(
        id="valvula_5_2",
        name="Válvula direccional 5/2",
        category="Neumática",
        width=56, height=44,
        description="Válvula direccional neumática 5/2",
        primitives=[
            _R(-22, -16, 20, 32),
            _R(2, -16, 20, 32),
            _L(-14, 6, -2, -6),
            _L(10, -6, 22, 6),
            _L(-22, -8, -28, -8), _P(-28, -8),
            _L(-22, 8, -28, 8), _P(-28, 8),
            _L(22, -8, 28, -8), _P(28, -8),
            _L(22, 8, 28, 8), _P(28, 8),
            _L(0, -16, 0, -22), _P(0, -22),
        ],
    ))

    symbols.append(Symbol(
        id="valvula_caudal",
        name="Válvula reguladora de caudal",
        category="Neumática",
        width=36, height=28,
        description="Válvula estranguladora / reguladora de caudal",
        primitives=[
            _C(0, 0, 14),
            _L(-12, 8, 12, -8),
            _L(-18, 0, -14, 0), _P(-18, 0),
            _L(14, 0, 18, 0), _P(18, 0),
        ],
    ))

    symbols.append(Symbol(
        id="valvula_nr_neum",
        name="Válvula antirretorno neumática",
        category="Neumática",
        width=48, height=20,
        description="Válvula antirretorno de aire comprimido",
        primitives=[
            _L(-24, 0, -8, 0),
            _L(-8, 0, 6, -10), _L(-8, 0, 6, 10), _L(6, -10, 6, 10),
            _L(6, 0, 10, -3),
            _L(10, -3, 14, 3),
            _L(14, 3, 18, -3),
            _L(18, -3, 22, 0),
            _L(22, 0, 24, 0),
            _P(-24, 0), _P(24, 0),
        ],
    ))

    symbols.append(Symbol(
        id="unidad_mantenimiento",
        name="Unidad de mantenimiento (FRL)",
        category="Neumática",
        width=64, height=46,
        description="Filtro + regulador + lubricador de aire comprimido",
        primitives=[
            _R(-9, -24, 18, 14),
            _L(-6, -20, 6, -12),
            _C(0, 0, 8),
            _L(0, -10, 0, -8),
            _L(0, 8, 0, 14), _P(0, 14),
            _L(0, -32, 0, -24), _P(0, -32),
            _L(8, 0, 14, -6),
            _L(14, -6, 14, 6),
            _L(14, 6, 18, 0),
        ],
    ))

    symbols.append(Symbol(
        id="deposito_aire",
        name="Depósito de aire comprimido",
        category="Neumática",
        width=32, height=38,
        description="Calderín / depósito de aire comprimido",
        primitives=[
            _R(-16, -14, 32, 26),
            _L(-16, -4, 16, -4),
            _L(0, -14, 0, -20), _P(0, -20),
            _L(0, 12, 0, 18), _P(0, 18),
        ],
    ))

    # ---------- Climatización y calefacción ----------
    symbols.append(Symbol(
        id="caldera",
        name="Caldera de calefacción",
        category="Climatización y calefacción",
        width=48, height=50,
        description="Caldera generadora de calor (gas/agua)",
        primitives=[
            _R(-16, -22, 32, 44),
            _L(-16, 0, 16, 0),
            _L(-6, -16, -4, -12),
            _L(-4, -12, -2, -16),
            _L(-2, -16, 0, -12),
            _L(0, -12, 2, -16),
            _L(2, -16, 4, -12),
            _C(0, 10, 5),
            _L(0, 22, 0, 28), _P(0, 28),
            _L(-24, 0, -16, 0), _P(-24, 0),
        ],
    ))

    symbols.append(Symbol(
        id="radiador",
        name="Radiador de calefacción",
        category="Climatización y calefacción",
        width=32, height=48,
        description="Radiador de agua caliente",
        primitives=[
            _R(-16, -18, 32, 36),
            _L(-12, -14, -12, 14),
            _L(-4, -14, -4, 14),
            _L(4, -14, 4, 14),
            _L(12, -14, 12, 14),
            _L(-16, 0, 16, 0),
            _L(0, -18, 0, -24), _P(0, -24),
            _L(0, 18, 0, 24), _P(0, 24),
        ],
    ))

    symbols.append(Symbol(
        id="termo",
        name="Termo eléctrico / acumulador ACS",
        category="Climatización y calefacción",
        width=28, height=52,
        description="Termo eléctrico acumulador de agua sanitaria",
        primitives=[
            _R(-14, -20, 28, 40),
            _L(-14, 0, 14, 0),
            _L(-8, -14, 8, -6),
            _L(-8, -6, 8, -14),
            _L(0, -20, 0, -26), _P(0, -26),
            _L(0, 20, 0, 26), _P(0, 26),
        ],
    ))

    symbols.append(Symbol(
        id="bomba_circulacion",
        name="Bomba de circulación",
        category="Climatización y calefacción",
        width=40, height=30,
        description="Bomba de circulación de agua (circuito de calefacción)",
        primitives=[
            _C(0, 0, 15),
            _L(1, -12, 1, 12),
            _L(1, -12, -3, -6),
            _L(1, -12, 5, -6),
            _L(-20, 0, -15, 0), _P(-20, 0),
            _L(15, 0, 20, 0), _P(20, 0),
        ],
    ))

    symbols.append(Symbol(
        id="fancoil",
        name="Fancoil / climatizador",
        category="Climatización y calefacción",
        width=44, height=30,
        description="Unidad fancoil o climatizador",
        primitives=[
            _R(-18, -15, 36, 30),
            _C(0, 0, 6),
            _L(-6, 0, 6, 0),
            _L(0, -6, 0, 6),
            _L(-18, 0, -22, 0), _P(-22, 0),
            _L(18, 0, 22, 0), _P(22, 0),
        ],
    ))

    symbols.append(Symbol(
        id="compresor_frio",
        name="Compresor de refrigeración",
        category="Climatización y calefacción",
        width=40, height=34,
        description="Compresor de circuito frigorífico",
        primitives=[
            _C(0, 0, 17),
            _L(2, -10, 2, 10),
            _L(2, -10, 15, 0),
            _L(2, 10, 15, 0),
            _L(-20, 0, -17, 0), _P(-20, 0),
            _L(17, 0, 20, 0), _P(20, 0),
        ],
    ))

    symbols.append(Symbol(
        id="ventilador",
        name="Ventilador / circulación de aire",
        category="Climatización y calefacción",
        width=26, height=26,
        description="Ventilador de impulsión de aire",
        primitives=[
            _C(0, 0, 12),
            _L(0, 0, 10, 6),
            _L(0, 0, -10, 6),
            _L(0, 0, 0, -12),
            _C(0, 0, 2),
        ],
    ))

    symbols.append(Symbol(
        id="valvula_3vias",
        name="Válvula mezcladora de 3 vías",
        category="Climatización y calefacción",
        width=36, height=36,
        description="Válvula mezcladora de tres vías",
        primitives=[
            _C(0, 0, 12),
            _L(-18, 0, -12, 0), _P(-18, 0),
            _L(12, 0, 18, 0), _P(18, 0),
            _L(0, -12, 0, -18), _P(0, -18),
            _L(0, 12, 0, 18), _P(0, 18),
            _L(0, 5, -8, -8),
        ],
    ))

    symbols.append(Symbol(
        id="manometro_cal",
        name="Manómetro de calefacción",
        category="Climatización y calefacción",
        width=28, height=34,
        description="Manómetro de presión del circuito",
        primitives=[
            _C(0, -2, 13),
            _L(0, -2, 8, -9),
            _L(0, -15, 0, -22), _P(0, -22),
        ],
    ))

    symbols.append(Symbol(
        id="termometro_cal",
        name="Termómetro de circuito",
        category="Climatización y calefacción",
        width=16, height=26,
        description="Termómetro de calefacción / ACS",
        primitives=[
            _C(0, 6, 6),
            _L(0, 12, 0, 20),
            _L(-7, 20, 7, 20),
            _L(-3, 13, 3, 13),
        ],
    ))

    return symbols


def symbol_by_id(symbols: List[Symbol], symbol_id: str) -> Symbol:
    for s in symbols:
        if s.id == symbol_id:
            return s
    raise KeyError(f"Símbolo no encontrado: {symbol_id}")


def categories(symbols: List[Symbol]) -> List[str]:
    seen: List[str] = []
    for s in symbols:
        if s.category not in seen:
            seen.append(s.category)
    return seen
