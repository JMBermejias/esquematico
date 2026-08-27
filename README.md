# Esquemático ⚡

Generador **visual** de esquemas eléctricos de cuadros e instalaciones,
unifilares y esquemáticos, para Windows.

Interfaz sencilla de arrastrar-y-soltar con una **paleta de símbolos
eléctricos** a la izquierda y un **lienzo** donde montar el circuito.

## Características

- 🧩 **Biblioteca de símbolos** listos para usar: interruptores
  magnetotérmicos (1P/2P/3P), diferenciales, fusibles, contactores,
  pulsadores, relés térmicos, motores, lámparas, enchufes, resistencias,
  condensadores, transformadores, tomas de tierra, redes de alimentación,
  bobinas, temporizadores, cuadros, etiquetas y nudos.
- 🖱️ **Edición totalmente visual**: coloca símbolos con un clic, arrástralos,
  rótalos (doble clic o `R`), redimensiona, cambia color y etiqueta.
- 🔗 **Herramienta de cableado**: dibuja cables entre los puntos de conexión
  de cada símbolo, con **ajuste a la cuadrícula** y *snapping* a pines.
- 🗂️ **Guardar / cargar** proyectos (formato `.esq`, JSON).
- 🖼️ **Exportar** a imagen **PNG** y a **PDF**.
- 🎨 Interfaz **azul claro**, clara e intuitiva.

## Instalación (usuarios finales)

Descarga la última versión desde **Release**:

| Opción                          | Descripción                                        |
| ------------------------------- | -------------------------------------------------- |
| `Instalador-Esquematico-*.exe`  | Instalador de Windows (Inno Setup). Instala en `Program Files`, crea accesos directos y asocia archivos `.esq`. |
| `Esquematico-portable.zip`      | Versión portable. Descomprime y ejecuta `Esquematico.exe`. No requiere instalación. |

## Requisitos

- Windows de 64 bits.
- No se requiere ningún otro software (todas las dependencias van incluidas).

## Desarrollo (compilar desde el código fuente)

Requiere **Python 3.9 o superior** y Windows o Linux.

```bash
git clone https://github.com/TU_USUARIO/esquematico.git
cd esquematico

# Crea un entorno virtual
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux

# Instala dependencias
pip install -r requirements.txt

# Ejecutar en modo desarrollo
python run.py
```

## Crear el ejecutable y el instalador (Windows)

Se necesita [PyInstaller](https://pyinstaller.org/) e
[Inno Setup 6](https://jrsoftware.org/isdl.php) instalado.

```powershell
# 1. Instalar dependencias de construcción
pip install pyinstaller

# 2. Construir todo: exe + portable.zip + instalador .exe
.\scripts\build.ps1

# Solo el ejecutable/contenedor y portable (sin instalador):
.\scripts\build.ps1 -SkipInstaller

# Solo el instalador (si ya compilaste con PyInstaller):
.\scripts\build.ps1 -NoPyInstaller -SkipPortable
```

La salida se genera en `dist/`:

- `dist/Esquematico/` — carpeta ejecutable (contenido del programa)
- `dist/Esquematico-portable.zip` — versión portable
- `dist/Instalador-Esquematico-<versión>.exe` — instalador

## Publicar una Release en GitHub automáticamente

El repositorio incluye un flujo de trabajo de GitHub Actions
(`.github/workflows/release.yml`) que, al crear un *tag* con prefijo `v`
(por ejemplo `v1.0.0`), compila el ejecutable, crea el paquete portable y el
instalador de Windows, y los publica como **Release** con todos los archivos
y dependencias necesarios.

```bash
git tag v1.0.0
git push origin v1.0.0
```

## Estructura del proyecto

```
esquematico/
├── esquematico/
│   ├── __main__.py          # Punto de entrada
│   ├── core/
│   │   ├── model.py         # Modelo de datos (diagrama, símbolos, cables)
│   │   └── renderer.py      # Renderizado a PNG/PDF
│   ├── symbols/
│   │   └── library.py       # Biblioteca de símbolos eléctricos
│   ├── ui/
│   │   ├── main_window.py   # Ventana principal y estilos
│   │   ├── canvas.py        # Lienzo interactivo
│   │   ├── palette.py       # Paleta de símbolos
│   │   └── properties.py    # Panel de propiedades
│   └── resources/           # Iconos
├── scripts/
│   ├── build.ps1            # Script de compilación
│   └── installer.iss        # Script de Inno Setup
├── .github/workflows/
│   └── release.yml          # Publicación automática de Releases
├── requirements.txt
├── Esquematico.spec         # Especificación de PyInstaller
└── run.py                   # Lanzador de desarrollo
```

## Licencia

[GNU General Public License v3.0 (GPL-3.0)](LICENSE)

Copyright (C) 2026 Jose Manuel Bernabeu Mejias
