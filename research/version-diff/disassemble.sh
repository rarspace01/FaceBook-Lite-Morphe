#!/usr/bin/env bash
# Disassembles one Facebook Lite version (primary dex from the APK plus the decoded secondary dex files)
# into a smali tree, with baksmali fetched from Google's Maven repository on first use.
#
# Usage: ./disassemble.sh <facebook-lite.apk> <decoded-dex-dir> <smali-outdir>
#   decoded-dex-dir is the output of ../superpack/decode.sh.
# Needs: a JDK, Maven (mvn), unzip.
set -euo pipefail
[ $# -eq 3 ] || { sed -n 2,7p "$0"; exit 2; }
HERE=$(cd "$(dirname "$0")" && pwd)
APK=$(realpath "$1"); DEX=$(realpath "$2"); OUT=$(realpath -m "$3")
LIB="$HERE/out/baksmali"
if [ ! -f "$LIB/smali-baksmali-3.0.7.jar" ]; then
  mkdir -p "$HERE/out/pom"
  cat > "$HERE/out/pom/pom.xml" <<'POM'
<project><modelVersion>4.0.0</modelVersion><groupId>x</groupId><artifactId>x</artifactId><version>1</version>
<repositories><repository><id>google</id><url>https://dl.google.com/android/maven2</url></repository></repositories>
<dependencies><dependency><groupId>com.android.tools.smali</groupId><artifactId>smali-baksmali</artifactId><version>3.0.7</version></dependency></dependencies></project>
POM
  (cd "$HERE/out/pom" && mvn -q -U dependency:copy-dependencies -DoutputDirectory="$LIB")
fi
T=$(mktemp -d); trap 'rm -rf "$T"' EXIT
unzip -q -o "$APK" 'classes*.dex' -d "$T"
for f in "$T"/classes*.dex "$DEX"/*.dex; do
  JAVA_TOOL_OPTIONS= java -cp "$LIB/*" com.android.tools.smali.baksmali.Main d -o "$OUT" "$f"
done
echo "$(find "$OUT" -name '*.smali' | wc -l) classes in $OUT"
