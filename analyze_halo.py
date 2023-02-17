#!/usr/bin/env python

# Read a .pcap file full of UDP packets from a velodyne and play them back to
# localhost:2368, for consumption by the velodyne driver.
#
# TODO: error-checking and options (looping, etc.)

import dpkt
import sys
import socket
import time

def form_byte(pkt, start, end=-1, little=True, signed=False):
    if end == -1:
        end = start
    out = 0
    shift = 0 if little else 8*(end-start)
    try:
        for i in range(start, end + 1):
            out += int(pkt[i]) << shift
            if little:
                shift += 8
            else:
                shift -= 8
        return out
    except:
        print("Error:", len(pkt))
        raise ValueError(f"Index")


def form_hex(data):
    for i in range(0, len(data), 16):
        # f"{form_byte(velodata, i, i):02x}"
        out = []
        out.extend([f"{x:02x}" for x in data[i:i+8]])
        out.extend([f"{x:02x}" for x in data[i+8:i+16]])
        print(" ".join(out))


def process_packet(data):
    d_tot = data[8:]
    sc = 0
    # form_hex(d_tot)
    for di in range(0, len(d_tot), 536):
        sc += 1
        d = d_tot[di:di + 536]
        header_len = form_byte(d, 0)
        h = d[:header_len]  # header
        # form_hex(h)
        hits = d[header_len:]
        # form_hex(hits)
        out = []
        conf = {"HeaderLen": form_byte(h, 0),
                "Status": form_byte(h, 1),
                "scanNum": form_byte(h, 2, 3),
                "largeRange": form_byte(h, 6, 7),
                "angle": form_byte(h, 8, 9),
                "heading": form_byte(h, 10, 11),
                "smallRange": form_byte(h, 12, 13),
                "rotation": form_byte(h, 14, 15),
                }
        for k, v in conf.items():
            out.append(f"{k}: {str(v).ljust(4)}")
        # out.append("\n")
        print(" ".join(out))
    print(sc)


UDP_IP = "localhost"
UDP_PORT = 2368
SOURCE_IP = '192.168.1.120'  # check correct
MIN_LEN = 1400
spokes_per_packet = 32


def parse(fname):
    lasttime = -1
    #sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    #i = 0
    max_count = 200
    count = 0
    more_fragments = 0
    with open(fname, "rb") as f:
        pcap = dpkt.pcap.Reader(f)
        data = bytearray()
        fragment_count = 0
        for ts, buf in pcap:
            eth = dpkt.ethernet.Ethernet(buf)
            if eth.type == dpkt.ethernet.ETH_TYPE_IP:
                ip = eth.data
                if more_fragments:
                    if type(ip.data) == bytes:
                        if fragment_count >= 10:
                            more_fragments = 0
                            fragment_count = 0
                            data.extend(ip.data)
                        else:
                            more_fragments = ip.mf
                            fragment_count += 1
                            data.extend(ip.data)
                            continue

                if ip.p == dpkt.ip.IP_PROTO_UDP:
                    udp = ip.data
                    ip_src_str = ".".join([str(int(x)) for x in ip.src])
                    if type(udp) == dpkt.udp.UDP:
                        velodata = udp.data

                        if ip_src_str == SOURCE_IP:
                            if len(velodata) > MIN_LEN:
                                more_fragments = ip.mf

                                data.extend(velodata)
                    elif len(data) > 0:
                        #form_hex(data)
                        process_packet(data)

                        data = bytearray()




                                

            # if lasttime > 0 and (ts-lasttime) > 0:
            #     time.sleep(ts-lasttime)
            # lasttime = ts
            # print('[%d] [%s] sending %d-byte message'%(i,`ts`,len(velodata)))
            # sock.sendto(velodata, (UDP_IP, UDP_PORT))
            # i += 1


if __name__ == '__main__':
    log_path = "eenx_logs/goodlog2.pcap"
    parse(log_path)
