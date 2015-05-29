#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import sys

BYTELEN = 8
SYNC_LEN = 32
TRAILER_LEN = 4

def process_pkt(pkt):
    p = "".join(pkt)
    try:
        p = p[p.index("111")-3:]
    except ValueError:
        return p
    new_p = []
    syncword, p = p[:SYNC_LEN], p[SYNC_LEN:]
    trailer, p = p[:TRAILER_LEN], p[TRAILER_LEN:]
    while p:
        new_p.append( "".join( reversed(p[:BYTELEN]) ) )
        p = p[BYTELEN:]
    new_p = ["%02X" % int(e, 2) for e in new_p]
    return "%08X (%s) %s" % (int("".join(reversed(syncword)) or "0",2), "".join(trailer), " ".join(new_p))
    #return "%s (%s) %s" % ("".join(syncword), "".join(trailer), " ".join(new_p))


if __name__ == "__main__":
    with file(sys.argv[1], "r") as fp:
        for line in fp:
            print process_pkt(line.strip())
