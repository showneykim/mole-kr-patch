#!/usr/bin/env python3
"""UE LocRes v3 (Optimized_CityHash64_UTF16) string-table editor.
Strategy: keep header + entries blob verbatim; only the trailing localized
string table holds display text, so we round-trip everything else byte-exact
and only rewrite strings we choose to translate."""
import struct, sys, json

MAGIC = bytes([0x0e,0x14,0x74,0x75,0x67,0x4a,0x03,0xfc,0x4a,0x15,0x90,0x9d,0xc3,0x37,0x7f,0x1b])

def read_fstr(b, p):
    n = struct.unpack_from('<i', b, p)[0]; p += 4
    if n == 0:   return ("", 'ansi', p)
    if n < 0:
        cnt = -n; raw = b[p:p+2*cnt]; p += 2*cnt
        return (raw[:-2].decode('utf-16-le'), 'utf16', p)
    raw = b[p:p+n]; p += n
    return (raw[:-1].decode('latin-1'), 'ansi', p)

def write_fstr(s, enc):
    if s == "": return struct.pack('<i', 0)
    if enc == 'ansi' and all(ord(c) < 256 for c in s):
        raw = s.encode('latin-1') + b'\x00'
        return struct.pack('<i', len(raw)) + raw
    raw = s.encode('utf-16-le') + b'\x00\x00'
    return struct.pack('<i', -(len(raw)//2)) + raw

def load(path):
    d = open(path, 'rb').read()
    assert d[:16] == MAGIC, "bad magic"
    ver = d[16]
    str_off = struct.unpack_from('<q', d, 17)[0]
    header = d[:25]                 # magic(16)+ver(1)+offset(8)
    entries = d[25:str_off]         # opaque: namespace/key index table
    p = str_off
    count = struct.unpack_from('<I', d, p)[0]; p += 4
    strings = []
    for _ in range(count):
        s, enc, p = read_fstr(d, p)
        ref = struct.unpack_from('<i', d, p)[0]; p += 4
        strings.append([s, enc, ref])
    assert p == len(d), f"trailing bytes: {p} != {len(d)}"
    return dict(ver=ver, header=header, entries=entries, strings=strings, raw=d)

def dump(doc):
    out = bytearray()
    out += doc['header'][:17]                       # magic + version
    off_pos = len(out)
    out += struct.pack('<q', 0)                      # offset placeholder
    out += doc['entries']
    str_off = len(out)
    out += struct.pack('<I', len(doc['strings']))
    for s, enc, ref in doc['strings']:
        out += write_fstr(s, enc) + struct.pack('<i', ref)
    struct.pack_into('<q', out, off_pos, str_off)
    return bytes(out)

if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'check':
        doc = load(sys.argv[2])
        rebuilt = dump(doc)
        print(f"ver={doc['ver']} strings={len(doc['strings'])} "
              f"orig={len(doc['raw'])} rebuilt={len(rebuilt)} identical={rebuilt==doc['raw']}")
    elif cmd == 'export':                            # -> json of [idx,text]
        doc = load(sys.argv[2])
        data = [[i, s[0]] for i, s in enumerate(doc['strings'])]
        json.dump(data, open(sys.argv[3], 'w'), ensure_ascii=False, indent=0)
        print(f"exported {len(data)} strings -> {sys.argv[3]}")
