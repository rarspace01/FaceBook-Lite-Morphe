"""Copies an Android .so with its symbol version tags (DT_VERSYM, DT_VERNEED, DT_VERNEEDNUM, DT_VERDEF,
DT_VERDEFNUM) neutralised, so glibc's loader binds its "malloc@LIBC"-style imports to unversioned
definitions instead of refusing them. Usage: unversion.py <in.so> <out.so>"""
import sys, struct
d = bytearray(open(sys.argv[1], 'rb').read())
phoff, = struct.unpack_from('<Q', d, 0x20); phentsize, phnum = struct.unpack_from('<HH', d, 0x36)
for i in range(phnum):
    o = phoff + i * phentsize
    t, fl, off, va, pa, fs, ms, al = struct.unpack_from('<IIQQQQQQ', d, o)
    if t == 2:
        for j in range(0, fs, 16):
            tag, = struct.unpack_from('<q', d, off + j)
            if tag in (0x6ffffff0, 0x6ffffffe, 0x6fffffff, 0x6ffffffc, 0x6ffffffd):
                struct.pack_into('<q', d, off + j, 0x6ffffd00); print('patched', hex(tag))
open(sys.argv[2], 'wb').write(d)
