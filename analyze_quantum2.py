#!/usr/bin/env python

# Read a .pcap file full of UDP packets from a velodyne and play them back to
# localhost:2368, for consumption by the velodyne driver.
#
# TODO: error-checking and options (looping, etc.)

import dpkt
import sys
import socket
import time

def form_byte(pkt, start, end, little=True, signed=False):
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
            print(len(pkt))
            raise ValueError(f"Index")

UDP_IP = "localhost"
UDP_PORT = 2368
SOURCE_IP = '198.18.0.249' # check correct

def parse(fname):
    lasttime = -1
    #sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    #i = 0
    with open(fname, "rb") as f:
        pcap = dpkt.pcapng.Reader(f)
        for ts, buf in pcap:
            eth = dpkt.ethernet.Ethernet(buf)
            ip = eth.data
            if type(ip) == dpkt.ip.IP:
                ip_src_str = ".".join([str(int(x)) for x in ip.src])
                udp = ip.data
                if type(udp) == dpkt.udp.UDP:
                    velodata = udp.data
                    if ip_src_str == SOURCE_IP:
                        
                        data_type = form_byte(velodata, 0, 3)
                        tot_len = len(velodata)
                        
                        if data_type == 0x00280003:
                            out = []
                            seq_num = form_byte(velodata, 4, 5)
                            scan_len = form_byte(velodata, 8, 9)
                            num_spokes = form_byte(velodata, 10, 11)
                            returns_per_range = form_byte(velodata, 14, 15)
                            azimuth = form_byte(velodata, 16, 17)
                            data_len = form_byte(velodata, 18, 19)
                            conf = {"SeqN": seq_num, "ScanL": scan_len, "NumSp": num_spokes, "RpR": returns_per_range, "AZi": azimuth, "DatL": data_len, "TotL": tot_len}
                            for k,v in conf.items():
                                out.append(f"{k}: {str(v).ljust(4)}")
                            out.append(" || ")
                            for i in range(20,20+data_len):
                                out.append(f"{form_byte(velodata, i, i):02x}")

                            print(" ".join(out))
                                

            # if lasttime > 0 and (ts-lasttime) > 0:
            #     time.sleep(ts-lasttime)
            # lasttime = ts
            # print('[%d] [%s] sending %d-byte message'%(i,`ts`,len(velodata)))
            # sock.sendto(velodata, (UDP_IP, UDP_PORT))
            # i += 1

if __name__ == '__main__':
    log_path = "logs/quantum_1.pcap"
    parse(log_path)