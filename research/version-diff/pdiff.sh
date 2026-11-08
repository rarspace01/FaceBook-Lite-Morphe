#!/usr/bin/env bash
# Diffs one class across versions with obfuscated class names normalised, so only member renames and
# real code changes show. No output means the class is unchanged apart from its name.
# Usage: ./pdiff.sh <old-smali-dir> <new-smali-dir> <old-class> <new-class>   e.g. ... X/0e1 X/0eT
set -euo pipefail
[ $# -eq 4 ] || { sed -n 2,4p "$0"; exit 2; }
n() { sed -E 's#LX/[^;]+;#LX;#g; /^[[:space:]]*\.line/d; /^[[:space:]]*$/d' "$1"; }
diff <(n "$1/$3.smali") <(n "$2/$4.smali")
