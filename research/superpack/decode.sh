#!/usr/bin/env bash
# Decodes Facebook Lite's secondary dex store on x86_64 Linux, without a phone, using the app's own
# superpack library under a small bionic-to-glibc shim. See README.md.
#
# Usage: ./decode.sh <facebook-lite.apk> <outdir> [apk-with-x86_64-lib]
#   The library must be the x86_64 build. When the APK is arm64-only, pass an x86_64 APK as the third
#   argument; a library from a newer version also decoded older stores in testing, and every file is
#   checked against the APK's own metadata.txt SHA-1s either way.
# Needs: gcc, a JDK (javac, java), unzip, python3.
set -euo pipefail
cd "$(dirname "$0")"
[ $# -ge 2 ] || { sed -n 2,9p "$0"; exit 2; }
APK=$(realpath "$1"); OUT=$(realpath -m "$2"); LIBAPK=$(realpath "${3:-$1}")
[ "$(uname -m)" = x86_64 ] || { echo "Needs an x86_64 Linux host" >&2; exit 2; }
JAVA_HOME=${JAVA_HOME:-$(dirname "$(dirname "$(readlink -f "$(command -v javac)")")")}
W=out/work; rm -rf "$W" && mkdir -p "$W/apk" "$W/lib" "$W/cls"

unzip -q -o "$APK" 'assets/secondary-program-dex-jars/*' -d "$W/apk"
unzip -q -o -j "$LIBAPK" 'lib/x86_64/libsuperpack-jni.so' -d "$W/lib" \
  || { echo "No lib/x86_64/libsuperpack-jni.so in $LIBAPK" >&2; exit 1; }
python3 -I unversion.py "$W/lib/libsuperpack-jni.so" "$W/libsp.so" >/dev/null

gcc -shared -fPIC -O1 -o "$W/lib/libc.so" shim/bionic.c -ldl
gcc -shared -fPIC -o "$W/lib/liblog.so" shim/android.c
cp "$W/lib/liblog.so" "$W/lib/libandroid.so"
gcc -shared -fPIC -o "$W/lib/libdl.so" -x c /dev/null -Wl,--no-as-needed -ldl
gcc -shared -fPIC -I"$JAVA_HOME/include" -I"$JAVA_HOME/include/linux" -o "$W/libloader.so" shim/loader.c -ldl
javac -nowarn -d "$W/cls" $(find src -name '*.java')

A="$W/apk/assets/secondary-program-dex-jars"
SPK_LIB="$(realpath "$W/libsp.so")" LD_LIBRARY_PATH="$(realpath "$W/lib")" JAVA_TOOL_OPTIONS= \
  java -cp "$W/cls" app.fblite.research.superpack.DecodeStore \
  "$W/libloader.so" "$W/libsp.so" "$A/store-0.dex.spo" "$A/metadata.txt" "$OUT"
