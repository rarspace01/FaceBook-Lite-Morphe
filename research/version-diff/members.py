"""Proposes new names for fields and methods of a class pair.
Fields are aligned by their (access, type) sequence: obfuscated field names are handed out in order, so a
field added in the new version shifts the names after it. Long runs of one type (dozens of booleans) make
the alignment ambiguous; confirm those with crossref.py. Methods are matched by signature, then by how
alike their instruction sequences are.
Usage: members.py <old.pkl|dir> <new.pkl|dir> <old-class> <new-class> [member ...]
  A member is a field name (A2c) or m:<method name> (m:AF0). With no members, every field is listed."""
import os, sys, difflib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from smali import load, norm, descriptor


def field_map(a, b):
    fa = [(acc, n, norm(t)) for acc, n, t in a['fields']]
    fb = [(acc, n, norm(t)) for acc, n, t in b['fields']]
    sm = difflib.SequenceMatcher(None, [(x[0], x[2]) for x in fa], [(x[0], x[2]) for x in fb], autojunk=False)
    m = {}
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == 'equal':
            for k in range(i2 - i1):
                m[fa[i1 + k][1]] = (fb[j1 + k][1], fa[i1 + k][2])
    return m


def method_candidates(a, b, name):
    out = []
    for acc, n, p, r, _, ins in a['methods']:
        if n != name:
            continue
        cands = sorted(((difflib.SequenceMatcher(None, ins, y[5], autojunk=False).ratio(), y[1]) for y in b['methods']
                        if y[0] == acc and norm(y[2]) == norm(p) and norm(y[3]) == norm(r)), reverse=True)
        out.append(('%s(%s)%s' % (n, norm(p), norm(r)), cands[:3]))
    return out


if __name__ == '__main__':
    old, new = load(sys.argv[1]), load(sys.argv[2])
    a, b = old[descriptor(sys.argv[3])], new[descriptor(sys.argv[4])]
    fm = field_map(a, b)
    print('fields: %d -> %d' % (len(a['fields']), len(b['fields'])))
    for w in sys.argv[5:] or [n for _, n, _ in a['fields']]:
        if w.startswith('m:'):
            for sig, cands in method_candidates(a, b, w[2:]):
                print('  method', sig, '->', ', '.join('%s (%.2f)' % (n, s) for s, n in cands) or '?')
        else:
            print('  field ', w, '->', '%s (%s)' % fm[w] if w in fm else '? (not aligned)')
