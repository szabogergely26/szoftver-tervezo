#!/usr/bin/env bash
set -euo pipefail

ARCH="all"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

BUILD_CHANNEL="$(python3 -c "import sys; sys.path.insert(0, '$PROJECT_DIR'); from version_info import BUILD_CHANNEL; print(BUILD_CHANNEL)")"

# A csomagnév, a megjelenített alkalmazásnév és az APT-suite a BUILD_CHANNEL-től
# függ (version_info.py az egységes forrás) - így a stabil (main) és a preview
# csomag egymás mellett, ütközés nélkül telepíthető ugyanarra a gépre.
case "$BUILD_CHANNEL" in
    preview)
        PACKAGE_NAME="tervezo-preview"
        APP_DISPLAY_NAME="Tervező (Preview)"
        APT_SUITE="preview"
        ;;
    main)
        PACKAGE_NAME="tervezo"
        APP_DISPLAY_NAME="Tervező"
        APT_SUITE="stable"
        ;;
    *)
        echo "Hiba: .deb csomag csak 'main' vagy 'preview' BUILD_CHANNEL-ből építhető (kapott: $BUILD_CHANNEL)."
        exit 1
        ;;
esac

BUILD_DIR="$SCRIPT_DIR/build"
ROOT_DIR="$SCRIPT_DIR/root"
DIST_DIR="$SCRIPT_DIR/dist"

PACKAGE_DIR="$BUILD_DIR/package"
DEBIAN_DIR="$PACKAGE_DIR/DEBIAN"

echo "Projekt könyvtár: $PROJECT_DIR/"
echo "Build csatorna: $BUILD_CHANNEL"
echo "Csomag neve: $PACKAGE_NAME"

VERSION="$(python3 -c "import sys; sys.path.insert(0, '$PROJECT_DIR'); from version_info import APP_VERSION; print(APP_VERSION)")"
echo "Verzió: $VERSION"


rm -rf "$BUILD_DIR"
mkdir -p "$PACKAGE_DIR"
mkdir -p "$DEBIAN_DIR"
mkdir -p "$DIST_DIR"
rm -f "$DIST_DIR"/*.deb

# Root fájlok (launcher, .desktop) másolása - a .in végű fájlok sablonok,
# amikbe a csomagnév/kijelzett név behelyettesítődik, a végleges (nem .in,
# csatorna-specifikus) néven kerülnek a csomagba. Minden más fájl (pl.
# jövőbeli statikus root tartalom) változatlanul átmásolódik.
while IFS= read -r -d '' src_file; do
    rel_path="${src_file#"$ROOT_DIR"/}"
    if [[ "$rel_path" == *.in ]]; then
        dest_rel="${rel_path%.in}"
        # A .in fájl neve maga is "tervezo"-alapú (pl. usr/bin/tervezo.in,
        # tervezo.desktop.in) - a kimeneti fájlnevet is a csomagnévre cseréljük.
        dest_rel="$(echo "$dest_rel" | sed "s/tervezo/$PACKAGE_NAME/g")"
        dest_file="$PACKAGE_DIR/$dest_rel"
        mkdir -p "$(dirname "$dest_file")"
        sed \
            -e "s/\${PACKAGE_NAME}/$PACKAGE_NAME/g" \
            -e "s/\${APP_DISPLAY_NAME}/$APP_DISPLAY_NAME/g" \
            -e "s/\${APT_SUITE}/$APT_SUITE/g" \
            "$src_file" > "$dest_file"
    else
        dest_file="$PACKAGE_DIR/$rel_path"
        mkdir -p "$(dirname "$dest_file")"
        cp -a "$src_file" "$dest_file"
    fi
done < <(find "$ROOT_DIR" -type f -print0)

# Alkalmazás fájlok másolása
mkdir -p "$PACKAGE_DIR/usr/share/$PACKAGE_NAME"
mkdir -p "$PACKAGE_DIR/usr/share/doc/$PACKAGE_NAME"

cp -a "$PROJECT_DIR/main.py" "$PACKAGE_DIR/usr/share/$PACKAGE_NAME/"
cp -a "$PROJECT_DIR/config.py" "$PACKAGE_DIR/usr/share/$PACKAGE_NAME/"
cp -a "$PROJECT_DIR/version_info.py" "$PACKAGE_DIR/usr/share/$PACKAGE_NAME/"
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

# build_info.py beégetése statikus tartalommal (a build pillanatában érvényes
# commit hash + dátum) - a telepített csomagban NEM lesz .git mappa, ezért a
# forrásbeli build_info.py élő git-lekérdezős fallbackja itt nem működne.
BUILD_COMMIT="$(cd "$PROJECT_DIR" && git rev-parse --short HEAD 2>/dev/null || echo "ismeretlen")"
BUILD_DATE="$(cd "$PROJECT_DIR" && git log -1 --format=%cd --date=short 2>/dev/null || echo "ismeretlen")"
cat > "$PACKAGE_DIR/usr/share/$PACKAGE_NAME/build_info.py" <<EOF
"""Build-időben generált fájl - build_deb.sh írta felül, ne szerkeszd kézzel."""

BUILD_COMMIT: str = "$BUILD_COMMIT"
BUILD_DATE: str = "$BUILD_DATE"
EOF




sed \
    -e "s/\${PACKAGE_NAME}/$PACKAGE_NAME/g" \
    -e "s/\${VERSION}/$VERSION/g" \
    "$SCRIPT_DIR/control.in" > "$DEBIAN_DIR/control"

# Szoftverforrás (APT repo) automatikus regisztrálásához szükséges fájlok.
# A csatorna-specifikus névre töltjük ki és nevezzük át (l. postinst.in),
# hogy a stabil és a preview csomag APT-beállítása ne írja felül egymást.
mkdir -p "$PACKAGE_DIR/usr/share/$PACKAGE_NAME/apt-repo-setup"

cp "$SCRIPT_DIR/../apt/tervezo-archive-keyring.gpg" \
    "$PACKAGE_DIR/usr/share/$PACKAGE_NAME/apt-repo-setup/$PACKAGE_NAME-archive-keyring.gpg"

sed "s/\${PACKAGE_NAME}/$PACKAGE_NAME/g; s/\${APT_SUITE}/$APT_SUITE/g" \
    "$SCRIPT_DIR/../apt/tervezo.sources.in" \
    > "$PACKAGE_DIR/usr/share/$PACKAGE_NAME/apt-repo-setup/$PACKAGE_NAME.sources"

sed "s/\${PACKAGE_NAME}/$PACKAGE_NAME/g; s/\${APT_SUITE}/$APT_SUITE/g" \
    "$SCRIPT_DIR/../apt/tervezo.pref.in" \
    > "$PACKAGE_DIR/usr/share/$PACKAGE_NAME/apt-repo-setup/$PACKAGE_NAME.pref"

sed "s/\${PACKAGE_NAME}/$PACKAGE_NAME/g" "$SCRIPT_DIR/postinst.in" > "$DEBIAN_DIR/postinst"

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
