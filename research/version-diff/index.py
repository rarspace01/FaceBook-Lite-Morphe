"""Summarises a smali tree once, so match.py and members.py start fast.
Usage: index.py <smali-dir> <out.pkl>"""
import os, sys, pickle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from smali import index

pickle.dump(index(sys.argv[1]), open(sys.argv[2], 'wb'))
