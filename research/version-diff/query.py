"""Looks up crossref.py results.
Usage: query.py <map.json> <query>...
  X/0gp          -> the new name of a class
  X/0gp->A2c     -> votes for the new name of a member (a few votes, or split votes, need checking)"""
import json, sys

d = json.load(open(sys.argv[1]))
for q in sys.argv[2:]:
    if '->' not in q:
        print(q, '=>', d['pairs'].get(q.replace('.', '/'), '?'))
        continue
    cls, member = q.split('->')
    votes = d['members'].get(f'L{cls.replace(".", "/")};->{member}', {})
    print(q, '=>', ', '.join('%s (%d)' % kv for kv in sorted(votes.items(), key=lambda kv: -kv[1])[:3]) or '?')
