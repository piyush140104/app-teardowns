#!/usr/bin/env python3
"""In-memory ASAR query tool: list / cat / grep without unpacking to disk."""
import json, struct, os, sys, re

class Asar:
    def __init__(self, path):
        self.f = open(path, 'rb')
        hdr = self.f.read(16)
        jlen = struct.unpack('<I', hdr[12:16])[0]
        self.meta = json.loads(self.f.read(jlen).decode('utf8'))
        self.base = 16 + jlen
        self.index = {}
        self._walk(self.meta, '')
    def _walk(self, node, prefix):
        for name, child in node.get('files', {}).items():
            p = f"{prefix}/{name}" if prefix else name
            if 'files' in child:
                self._walk(child, p)
            elif 'offset' in child:
                self.index[p] = (int(child['offset']), child['size'])
    def read(self, path):
        off, size = self.index[path]
        self.f.seek(self.base + off)
        return self.f.read(size)
    def text(self, path):
        return self.read(path).decode('utf8', errors='replace')

def main():
    cmd, archive = sys.argv[1], sys.argv[2]
    a = Asar(archive)
    if cmd == 'list':
        pat = sys.argv[3] if len(sys.argv) > 3 else ''
        for p in sorted(a.index):
            if pat in p: print(f"{a.index[p][1]:>9}  {p}")
    elif cmd == 'cat':
        path = sys.argv[3]
        lo = int(sys.argv[4]) if len(sys.argv) > 4 else 1
        hi = int(sys.argv[5]) if len(sys.argv) > 5 else 10**9
        for i, l in enumerate(a.text(path).split('\n'), 1):
            if lo <= i <= hi: print(f"{i}\t{l}")
    elif cmd == 'grep':
        rx = re.compile(sys.argv[3])
        scope = sys.argv[4] if len(sys.argv) > 4 else ''
        excl = sys.argv[5] if len(sys.argv) > 5 else None
        for p in sorted(a.index):
            if scope not in p: continue
            if excl and excl in p: continue
            if not p.endswith(('.js', '.json', '.html', '.ts')): continue
            try: t = a.text(p)
            except Exception: continue
            for i, l in enumerate(t.split('\n'), 1):
                if rx.search(l): print(f"{p}:{i}: {l.strip()[:220]}")
    elif cmd == 'stats':
        import collections
        c = collections.Counter(); tot = 0
        for p, (o, s) in a.index.items():
            c[p.split('/')[0] if '/' in p else '(root)'] += 1; tot += s
        print(f"files={len(a.index)} bytes={tot}")
        for k, v in c.most_common(20): print(f"  {v:>5}  {k}")
main()
