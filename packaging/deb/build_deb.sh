#!/usr/bin/env bash
set -euo pipefail

PACKAGE_NAME="tervezo"
VERSION="0.3.0"
ARCH="all"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

BUILD_DIR="$SCRIPT_DIR/build"
ROOT_DIR="$SCRIPT_DIR/root"
DIST_DIR="$SCRIPT_DIR/dist"

PACKAGE_DIR="$BUILD_DIR/package"
DEBIAN_DIR="$PACKAGE_DIR/DEBIAN"

echo "Projekt könyvtár: $PROJECT_DIR/"
echo "Csomag neve: $PACKAGE_NAME"
echo "Verzió: $VERSION"


rm -rf "$BUILD_DIR"
mkdir -p "$PACKAGE_DIR"
mkdir -p "$DEBIAN_DIR"
mkdir -p "$DIST_DIR"
rm -f "$DIST_DIR"/*.deb

# Alap root fájlok (launcher, .desktop) másolása
cp -a "$ROOT_DIR/." "$PACKAGE_DIR/"

# Alkalmazás fájlok másolása
mkdir -p "$PACKAGE_DIR/usr/share/$PACKAGE_NAME"
mkdir -p "$PACKAGE_DIR/usr/share/doc/$PACKAGE_NAME"

cp -a "$PROJECT_DIR/main.py" "$PACKAGE_DIR/usr/share/$PACKAGE_NAME/"
cp -a "$PROJECT_DIR/config.py" "$PACKAGE_DIR/usr/share/$PACKAGE_NAME/"
cp -a "$PROJECT_DIR/tervezo" "$PACKAGE_DIR/usr/share/$PACKAGE_NAME/"
cp -a "$PROJECT_DIR/settings" "$PACKAGE_DIR/usr/share/$PACKAGE_NAME/"
cp -a "$PROJECT_DIR/assets" "$PACKAGE_DIR/usr/share/$PACKAGE_NAME/" 2>/dev/null || true
cp -a "$PROJECT_DIR/README.md" "$PACKAGE_DIR/usr/share/doc/$PACKAGE_NAME/README.md" 2>/dev/null || true

# Ikon telepítése hicolor alá
ICON_SRC="$PROJECT_DIR/assets/icons/app_icon.png"
ICON_DEST="$PACKAGE_DIR/usr/share/icons/hicolor/256x256/apps"
if [[ -f "$ICON_SRC" ]]; then
    mkdir -p "$ICON_DEST"
    cp "$ICON_SRC" "$ICON_DEST/$PACKAGE_NAME.png"
fi

cp "$SCRIPT_DIR/control" "$DEBIAN_DIR/control"

# Szoftverforrás (APT repo) automatikus regisztrálásához szükséges fájlok
mkdir -p "$PACKAGE_DIR/usr/share/$PACKAGE_NAME/apt-repo-setup"
cp "$SCRIPT_DIR/../apt/tervezo-archive-keyring.gpg" "$PACKAGE_DIR/usr/share/$PACKAGE_NAME/apt-repo-setup/"
cp "$SCRIPT_DIR/../apt/tervezo.sources" "$PACKAGE_DIR/usr/share/$PACKAGE_NAME/apt-repo-setup/"
cp "$SCRIPT_DIR/../apt/tervezo.pref" "$PACKAGE_DIR/usr/share/$PACKAGE_NAME/apt-repo-setup/"

cp "$SCRIPT_DIR/postinst" "$DEBIAN_DIR/postinst"

# Python cache-fájlok eltávolítása a csomagból
find "$PACKAGE_DIR" -type d -name "__pycache__" -prune -exec rm -rf {} +
find "$PACKAGE_DIR" -type f -name "*.pyc" -delete

# Egységes jogosultságok, hogy telepítés után bárki olvashassa/futtathassa.
# FONTOS: ez az EGYETLEN olyan blokk, ami jogosultságot állít, és ez fut le
# UTOLJÁRA a dpkg-deb --build előtt -- ha bármi mást ide adsz hozzá a jövőben,
# ami fájlt másol be a csomagba, a chmod-oknak ez után kell jönniük, különben
# a "find ... chmod 644" felülírja a futtathatósági jogokat.
find "$PACKAGE_DIR" -type d -exec chmod 755 {} \;
find "$PACKAGE_DIR" -type f -exec chmod 644 {} \;
chmod 755 "$PACKAGE_DIR/usr/bin/$PACKAGE_NAME"
chmod 755 "$DEBIAN_DIR/postinst"

OUTPUT_FILE="$DIST_DIR/${PACKAGE_NAME}_${ARCH}.deb"
dpkg-deb --root-owner-group --build "$PACKAGE_DIR" "$OUTPUT_FILE"

echo
echo "Elkészült:"
echo "$OUTPUT_FILE"
