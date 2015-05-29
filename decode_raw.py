#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import sys, struct, collections
from decode_pkt import process_pkt

FMT = struct.Struct("<h")
THRESH = 3000
STRONG_START = 50
STRONG_STOP = 2
RINGBUF_SIZE = 100
SAMP_RATE = 4e6
DATA_RATE = 1e6
CORR_LEN = long( (SAMP_RATE/DATA_RATE) * 20)
CORR_THRESH = THRESH * CORR_LEN

def corr_fn(i):
    return 2* int((i % ( 2 * SAMP_RATE / DATA_RATE)) / (SAMP_RATE / DATA_RATE))-1


def decode(fp):
    strong = 0
    ringbuf = [None] * RINGBUF_SIZE
    ringbuf_i = 0
    in_pkt = False
    pkt_started = False
    v = 0
    pos = 0
    time = 0
    last_time = 0
    last_corr_v = 0
    decode_v = 0
    sample_pos = 0
    dc = 0
    pkt = []
    pk = 0
    
    while True:
        try:
            v,  = FMT.unpack(fp.read(FMT.size))
        except:
            break
        
        ringbuf_oldval = ringbuf[ringbuf_i]
        ringbuf[ringbuf_i] = v
        
        if ringbuf_oldval is not None:
            if abs(ringbuf_oldval) >= THRESH:
                strong = strong - 1
        
        if abs(v) >= THRESH:
            strong = strong + 1
        
        if not in_pkt:
            if strong >= STRONG_START:
                print >>sys.stderr, "Packet at %fs, delta %fms" % (time, (time - last_time)*1e3), 
                in_pkt = True
                last_time = time
        else:
            if strong <= STRONG_STOP:
                print >>sys.stderr, "ended at %fs: %s" % (time, process_pkt("".join(pkt)))
                print "".join(pkt)
                in_pkt = False
                last_corr_v = 0
                pkt_started = False
                pkt = []
        
        if (pk > 0 and v <= 0) or (pk <= 0 and v > 0):
            pk = v
        if abs(v) > abs(pk):
            pk = v
        
        v = pk
        
        if in_pkt:
            if not pkt_started:
                corr_v = 0
                for i in range(CORR_LEN):
                    corr_v = corr_v + corr_fn(i) * (ringbuf[ (ringbuf_i - i + RINGBUF_SIZE - 1)%RINGBUF_SIZE ])
                if last_corr_v > CORR_THRESH and corr_v < last_corr_v:
                    pkt_started = pos
                    sample_pos = 2
                    decode_tmp = 0
                    decode_v = 0
                    dc = 0
                    for i in range(CORR_LEN/2):
                        dc = dc + (ringbuf[ (ringbuf_i - i + RINGBUF_SIZE - 1)%RINGBUF_SIZE ])
                    dc = dc / float(CORR_LEN/2)
                last_corr_v = corr_v
            else:
                #decode_tmp = decode_tmp + v - dc
                decode_tmp = decode_tmp + [-THRESH, THRESH][v > dc]
                sample_pos = sample_pos + 1
                if sample_pos >= int(SAMP_RATE/DATA_RATE):
                    decode_v = decode_tmp / sample_pos
                    decode_tmp = 0
                    sample_pos = sample_pos - int(SAMP_RATE/DATA_RATE)
                    pkt.append( ["0", "1"][decode_v>0] )
            
            
            #print pos, v, dc, decode_v
        
        ringbuf_i = (ringbuf_i + 1) % RINGBUF_SIZE
        pos = pos + 1
        time = float(pos) / SAMP_RATE
    

if __name__ == "__main__":
    with file(sys.argv[1], "rb") as fp:
        decode(fp)
    
