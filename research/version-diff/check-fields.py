"""Checks a field mapping: each old field and its proposed new field must have the same type, once the
old type's obfuscated class is translated with the class pairs given.
Usage: check-fields.py <old.pkl|dir> <new.pkl|dir> <mapping.txt> [classes old=new,...]
  mapping.txt: "OldClass oldField NewClass newField" lines, e.g. "X/0gp A2c X/0hd A2e", and
  "OldClass NewClass" lines for class pairs. Field types that are obfuscated classes are translated
  through every class pair in the file plus any given on the command line. Lines after # are ignored."""
import os, sys, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from smali import load, descriptor

old, new = load(sys.argv[1]), load(sys.argv[2])
lines = [l.split('#')[0].split() for l in open(sys.argv[3])]
rows = [l for l in lines if len(l) == 4]
pairs = {descriptor(l[0]): descriptor(l[1]) for l in lines if len(l) == 2}
pairs.update({descriptor(r[0]): descriptor(r[2]) for r in rows})
if len(sys.argv) > 4:
    pairs.update({descriptor(a): descriptor(b) for a, b in (p.split('=') for p in sys.argv[4].split(','))})
bad = 0
for oc, of, nc, nf in rows:
    ta = {n: t for _, n, t in old[descriptor(oc)]['fields']}.get(of)
    tb = {n: t for _, n, t in new[descriptor(nc)]['fields']}.get(nf)
    want = re.sub(r'L[^;]+;', lambda m: pairs.get(m.group(0), m.group(0)), ta) if ta else None
    ok = ta is not None and want == tb
    bad += not ok
    print('%-5s %s.%s %s -> %s.%s %s' % ('OK' if ok else 'CHECK', oc, of, ta, nc, nf, tb))
sys.exit(1 if bad else 0)
