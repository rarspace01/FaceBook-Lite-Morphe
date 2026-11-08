"""Maps classes and members across versions from how the code uses them.
For each known class pair, every old method is aligned with its best new counterpart, instruction by
instruction, with obfuscated names normalised. Where the code lines up, the old and new names it
references are counted as votes: field Foo->A2c and Bar->A2e in the same place is one vote for
A2c -> A2e. Class names found this way become new pairs for the next round.
Usage: crossref.py <old-smali-dir> <new-smali-dir> <seed> <out.json> [rounds=2]
  seed: comma-separated old=new pairs, e.g. X/1DY=X/1E8,X/0gp=X/0hd (from match.py).
Read the result with query.py. A round over ~1000 classes takes some minutes."""
import sys, os, re, difflib, collections, json

REF = re.compile(r'(L[^;\s]+;)->([^\s(:]+)')
SKIP = ('.line', '.local', '.param', '.end param', '.end local', '.restart')


def methods(path):
    txt = open(path, encoding='utf8').read()
    out = {}
    for m in re.finditer(r'^\.method (.*?)(\S+)\((.*?)\)(\S+)\n(.*?)^\.end method', txt, re.M | re.S):
        lines = [l.strip() for l in m.group(5).split('\n') if l.strip() and not l.strip().startswith(SKIP)]
        key = (m.group(1).strip(), re.sub(r'LX/[^;]+;', 'LX;', m.group(3) + ')' + m.group(4)))
        out.setdefault(key, []).append(lines)
    return out


def shape(line):
    """The line with references' member names blanked and obfuscated class names normalised."""
    line = REF.sub(lambda m: ('LX;' if m.group(1).startswith('LX/') else m.group(1)) + '->#', line)
    return re.sub(r'LX/[^;]+;', 'LX;', line)


def compare(old_dir, new_dir, o, n, members, classes):
    po, pn = f'{old_dir}/{o}.smali', f'{new_dir}/{n}.smali'
    if not (os.path.exists(po) and os.path.exists(pn)):
        return
    ma, mb = methods(po), methods(pn)
    for key, bodies in ma.items():
        for la in bodies:
            if key not in mb:
                continue
            ka = [shape(l) for l in la]
            lb = max(mb[key], key=lambda y: difflib.SequenceMatcher(None, ka, [shape(l) for l in y], autojunk=False).ratio())
            kb = [shape(l) for l in lb]
            for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, ka, kb, autojunk=False).get_opcodes():
                if tag != 'equal':
                    continue
                for x, y in zip(la[i1:i2], lb[j1:j2]):
                    for r1, r2 in zip(REF.findall(x), REF.findall(y)):
                        members[r1][r2] += 1
                    for c1, c2 in zip(re.findall(r'LX/[^;]+;', x), re.findall(r'LX/[^;]+;', y)):
                        classes[c1][c2] += 1


if __name__ == '__main__':
    old_dir, new_dir, seed, out = sys.argv[1:5]
    rounds = int(sys.argv[5]) if len(sys.argv) > 5 else 2
    pairs = dict(p.split('=') for p in seed.split(','))
    members = collections.defaultdict(collections.Counter)
    classes = collections.defaultdict(collections.Counter)
    done = set()
    for r in range(rounds):
        for o, n in [(o, n) for o, n in pairs.items() if o not in done]:
            compare(old_dir, new_dir, o, n, members, classes)
            done.add(o)
        for c1, votes in classes.items():
            o = c1[1:-1]
            (c2, v), = votes.most_common(1)
            if o not in pairs and v >= 3 and v >= 0.8 * sum(votes.values()):
                pairs[o] = c2[1:-1]
        print('round %d: %d class pairs' % (r + 1, len(pairs)), file=sys.stderr)
    json.dump({'pairs': pairs,
               'members': {f'{a}->{b}': {f'{c}->{d}': v for (c, d), v in cnt.items()} for (a, b), cnt in members.items()}},
              open(out, 'w'))
