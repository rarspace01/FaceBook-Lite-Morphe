"""Finds the new version's counterpart of each given old class, by similarity of its shape: access flags,
superclass, interfaces, field and method signatures (obfuscated names normalised), method sizes, string
constants and calls into the Android/Java API. Prints the three best candidates with a 0..1 score; a clear
winner near 1.0 is usually right, close scores need checking by hand (pdiff.sh, members.py).
Usage: match.py <old.pkl|smali-dir> <new.pkl|smali-dir> <class>...   e.g. X/0gp"""
import os, sys, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from smali import load, norm, descriptor, OBF_MEMBER


def features(c):
    f = collections.Counter()
    f['acc:' + c['acc']] += 1
    f['super:' + norm(c['super'])] += 3
    for i in c['ifaces']:
        f['if:' + norm(i)] += 2
    for acc, _, t in c['fields']:
        f['F:' + acc + norm(t)] += 1
    for acc, n, p, r, count, _ in c['methods']:
        name = '' if OBF_MEMBER.match(n) else n
        f['M:%s%s(%s)%s' % (acc, name, norm(p), norm(r))] += 2
        f['MS:%s%d' % (name, count // 4)] += 1
    for s in c['strings']:
        f['S:' + s] += 3
    for r in c['refs']:
        f['R:' + r] += 1
    return f


def similarity(a, b):
    union = sum((a | b).values())
    return sum((a & b).values()) / union if union else 0


if __name__ == '__main__':
    old, new = load(sys.argv[1]), load(sys.argv[2])
    candidates = {k: features(v) for k, v in new.items() if k.startswith('LX/')}
    for name in sys.argv[3:]:
        name = descriptor(name)
        if name not in old:
            print(name, 'not in old version'); continue
        fa = features(old[name])
        best = sorted(((similarity(fa, v), k) for k, v in candidates.items()), reverse=True)[:3]
        print(name, '  '.join('%s=%.2f' % (k, s) for s, k in best))
