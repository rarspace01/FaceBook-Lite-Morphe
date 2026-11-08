"""Reads a smali tree into a per-class summary, shared by the other scripts. Obfuscated classes are
X/<3 characters>; norm() replaces their names so classes can be compared across versions."""
import os, re, pickle

XNAME = re.compile(r'LX/[^;]+;')
OBF_MEMBER = re.compile(r'^A[0-9A-Za-z]{2}$')


def norm(s):
    return XNAME.sub('LX;', s)


def parse_class(txt):
    cls = re.search(r'^\.class (.*?)(L\S+;)$', txt, re.M)
    c = {'name': cls.group(2), 'acc': cls.group(1).strip(),
         'super': re.search(r'^\.super (\S+)', txt, re.M).group(1),
         'ifaces': re.findall(r'^\.implements (\S+)', txt, re.M),
         'fields': re.findall(r'^\.field (.*?)(\S+):(\S+?)(?: = .*)?$', txt, re.M),
         'methods': [], 'strings': set(re.findall(r'const-string(?:/jumbo)? \S+, "(.*)"$', txt, re.M)), 'refs': set()}
    for m in re.finditer(r'^\.method (.*?)(\S+)\((.*?)\)(\S+)\n(.*?)^\.end method', txt, re.M | re.S):
        ins = [l.strip().split()[0] for l in m.group(5).split('\n')
               if l.strip() and not l.strip().startswith(('.', ':', '#'))]
        c['methods'].append((m.group(1).strip(), m.group(2), m.group(3), m.group(4), len(ins), tuple(ins)))
    for r in re.findall(r'(L[^;\s]+;->[^\s(:]+(?:\([^)]*\)\S+|:\S+))', txt):
        if not r.startswith('LX/'):
            c['refs'].add(norm(r))
    return c


def index(root):
    db = {}
    for dp, _, fs in os.walk(root):
        for f in fs:
            if f.endswith('.smali'):
                c = parse_class(open(os.path.join(dp, f), encoding='utf8').read())
                db[c['name']] = c
    return db


def load(path):
    """A smali directory, or a pickle written by index.py."""
    if os.path.isdir(path):
        return index(path)
    return pickle.load(open(path, 'rb'))


def descriptor(name):
    """X/0gp, X.0gp or LX/0gp; -> LX/0gp;"""
    name = name.replace('.', '/')
    return name if name.startswith('L') and name.endswith(';') else 'L' + name + ';'
