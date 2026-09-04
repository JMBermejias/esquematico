#!/usr/bin/env bash
# build-deb.sh — Builds Esquematico with PyInstaller and creates a .deb package
# Requirements: Python 3.9+, pip, pyinstaller, PySide6, dpkg-deb, fakeroot
# Usage: ./scripts/build-deb.sh [version]
# If no version is specified, it reads from esquematico/__init__.py

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

VERSION="${1:-$(python3 -c "from esquematico import __version__; print(__version__)")}"
PKG_NAME="esquematico"
ARCH="amd64"
DEB_NAME="${PKG_NAME}_${VERSION}_${ARCH}"
DIST_DIR="$PROJECT_DIR/dist"
BUILD_DIR="$DIST_DIR/$DEB_NAME"
DEB_FILE="$DIST_DIR/${DEB_NAME}.deb"

echo "=== Building Esquematico v${VERSION} for Debian ==="

# Clean previous builds
rm -rf "$BUILD_DIR" "$DIST_DIR/Esquematico" "$DIST_DIR/$DEB_NAME"*.deb

# ── 1. Build with PyInstaller ──
echo "[1/5] Building with PyInstaller..."
pyinstaller --noconfirm --clean \
    --name Esquematico \
    --noconsole \
    --add-data "esquematico/resources/icon.png:esquematico/resources" \
    --add-data "esquematico/resources/app.ico:esquematico/resources" \
    run.py

# ── 2. Prepare .deb directory structure ──
echo "[2/5] Preparing .deb structure..."
mkdir -p "$BUILD_DIR/DEBIAN"
mkdir -p "$BUILD_DIR/usr/bin"
mkdir -p "$BUILD_DIR/usr/lib/esquematico"
mkdir -p "$BUILD_DIR/usr/share/applications"
mkdir -p "$BUILD_DIR/usr/share/icons/hicolor/256x256/apps"
mkdir -p "$BUILD_DIR/usr/share/icons/hicolor/128x128/apps"
mkdir -p "$BUILD_DIR/usr/share/icons/hicolor/64x64/apps"
mkdir -p "$BUILD_DIR/usr/share/icons/hicolor/48x48/apps"

# Copy PyInstaller output
cp -r dist/Esquematico/* "$BUILD_DIR/usr/lib/esquematico/"
chmod 755 "$BUILD_DIR/usr/lib/esquematico/Esquematico"

# ── 3. Create launcher, .desktop, icons ──
echo "[3/5] Creating launcher and desktop entry..."

cat > "$BUILD_DIR/usr/bin/esquematico" << 'LAUNCHER'
#!/bin/sh
exec /usr/lib/esquematico/Esquematico "$@"
LAUNCHER
chmod 755 "$BUILD_DIR/usr/bin/esquematico"

for size in 256 128 64 48; do
    cp esquematico/resources/icon.png "$BUILD_DIR/usr/share/icons/hicolor/${size}x${size}/apps/esquematico.png"
done

cat > "$BUILD_DIR/usr/share/applications/esquematico.desktop" << 'DESKTOP'
[Desktop Entry]
Type=Application
Name=Esquematico
GenericName=Generador de esquemas electricos
Comment=Generador visual de esquemas electricos de cuadros e instalaciones, unifilares y esquematicos
Exec=/usr/lib/esquematico/Esquematico %F
Icon=esquematico
Terminal=false
Categories=Education;Engineering;Electronics;
MimeType=application/x-esquematico;
Keywords=electricidad;esquemas;electrotecnia;unifilar;
DESKTOP

# ── 4. Generate DEBIAN/control ──
echo "[4/5] Generating control file..."
INSTALLED_SIZE=$(du -sk "$BUILD_DIR" | cut -f1)

cat > "$BUILD_DIR/DEBIAN/control" << EOF
Package: ${PKG_NAME}
Version: ${VERSION}
Section: education
Priority: optional
Architecture: ${ARCH}
Depends: libgl1, libegl1, libfontconfig1, libdbus-1-3, libxcb-cursor0, libxcb-icccm4, libxcb-image0, libxcb-keysyms1, libxcb-randr0, libxcb-render-util0, libxcb-shape0, libxcb-xinerama0, libxcb-xkb1, libxkbcommon0
Installed-Size: ${INSTALLED_SIZE}
Maintainer: Jose Manuel Bernabeu Mejias <jmbernabeu@gmail.com>
Homepage: https://github.com/JMBermejias/esquematico
Description: Generador visual de esquemas electricos
 Esquematico es una aplicacion de escritorio para crear de forma visual
 esquemas electricos de cuadros e instalaciones, unifilares y esquematicos.
 Incluye una amplia biblioteca de simbolos electricos, neumaticos,
 hidraulicos y fotovoltaicos, con soporte para exportacion a PDF y
 asociacion de archivos .esq.
EOF

cat > "$BUILD_DIR/DEBIAN/postinst" << 'POSTINST'
#!/bin/sh
set -e
if [ "$1" = "configure" ]; then
    update-desktop-database /usr/share/applications 2>/dev/null || true
    gtk-update-icon-cache /usr/share/icons/hicolor 2>/dev/null || true
fi
POSTINST
chmod 755 "$BUILD_DIR/DEBIAN/postinst"

cat > "$BUILD_DIR/DEBIAN/postrm" << 'POSTRM'
#!/bin/sh
set -e
if [ "$1" = "remove" ]; then
    update-desktop-database /usr/share/applications 2>/dev/null || true
    gtk-update-icon-cache /usr/share/icons/hicolor 2>/dev/null || true
fi
POSTRM
chmod 755 "$BUILD_DIR/DEBIAN/postrm"

# ── 5. Build .deb ──
echo "[5/5] Building .deb package..."
fakeroot dpkg-deb --build --root-owner-group "$BUILD_DIR" "$DEB_FILE"

echo ""
echo "=== Done! ==="
echo "Package: $DEB_FILE"
echo "Size: $(du -h "$DEB_FILE" | cut -f1)"
echo ""
echo "To install:"
echo "  sudo dpkg -i $DEB_FILE"
echo "  sudo apt-get install -f  # if dependencies are missing"
