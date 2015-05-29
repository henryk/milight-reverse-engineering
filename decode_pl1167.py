#!/usr/bin/env python

import sys

def SPI_Frames(fp):
    fp = fp.__iter__()
    fp.next()
    framestart = None
    w_frame, r_frame = [], []
    frameno = None
    for line in fp:
        time, no, mosi, miso = line.split(",")
        if no:
            no = int(no, 0)
        if frameno != no:
            if frameno is not None:
                yield framestart, w_frame, r_frame
                w_frame, r_frame = [], []
            frameno = no
            framestart = float(time)
        w_frame.append(int(mosi, 16))
        r_frame.append(int(miso, 16))
    
    if frameno is not None:
        yield framestart, w_frame, r_frame

def decode_pl1667(framestart, w_frame, r_frame):
    if len(w_frame) < 3:
        print "Invalid frame: %r" % w_frame
        return
    
    op = w_frame[0]
    reg = op & 0x7f
    
    print "%12.8f:" % framestart, 
    
    if op&0x80:
        hi, lo = r_frame[1:3]
        print " Read reg %2X -> %02X %02X" % (reg, hi, lo), 
    else:
        hi, lo = w_frame[1:3]
        if reg == 0x32:
            print "Write FIFO: %s" % (" ".join("%02X" % e for e in w_frame[1:])), 
        else:
            print "Write reg %2X -> %02X %02X" % (reg, hi, lo), 
    

    data = hi<<8 | lo
    
    if reg == 0x7:
        if data & (1<<8): print "start TX,",  
        if data & (1<<7): print "start RX,", 
        print "channel %s (%s)MHz" % (data & 0x7F, 2402+ (data &0x7F)), 
    if reg == 0x20:
        print "preamble length: %i bytes," % ((data>>13)+1), 
        print "syncword length: %i bits," % (16*( ((data>>11)&0x3) + 1)), 
        print "trailer length: %i bits," % (2+(2*( ((data>>8)&0x7) + 1))), 
        print "data type: %s," % ["NRZ", "Manchester", "8/10 bits", "Interleave"][ (data>>6) & 0x3], 
        print "FEC: %s" % ["None", "FEC13", "FEC23", "Reserved"][ (data>>4) & 0x3], 
    if reg >= 0x24 and op <= 0x27:
        print "syncword %i: %04X" % (op - 0x24, data), 
    if reg == 0x29:
        if data & (1<<15): print "CRC on,", 
        if data & (1<<14): print "scramble on,", 
        if data & (1<<13): print "first byte is length,", 
        if data & (1<<12): print "FW_TERM_TX,", 
        if data & (1<<11): print "auto ack,", 
        print "initial CRC data: %02X" % lo, 
    if reg == 0x34:
        if data & (1<<15): print "clear FIFO TX,", 
        print "FIFO write pointer: %i," % ((data>>8)&0x6f), 
        if data & (1<<7): print "clear FIFO RX,", 
        print "FIFO read pointer: %i" % ((data>>0)&0x6f), 
    
    print

if __name__ == "__main__":
    for filename in sys.argv[1:]:
        with file(filename, "r") as fp:
            for framestart, w_frame, r_frame in SPI_Frames(fp):
                decode_pl1667(framestart, w_frame, r_frame)
