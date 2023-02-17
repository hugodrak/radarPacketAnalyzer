#from scapy.utils import PcapReader
from scapy.utils import RawPcapReader
from scapy.layers.l2 import Ether
from scapy.layers.inet import IP, UDP
import os
import numpy as np
import matplotlib.pyplot as plt
import math
import logging
from datetime import datetime
from matplotlib.animation import FFMpegWriter

from src.raymarine.RaymarineRecieve  import QuantumData

## Garmin xHD has 1440 spokes of varying 519 - 705 bytes each
#define GARMIN_XHD_SPOKES 1440
#define GARMIN_XHD_MAX_SPOKE_LEN 705
GARMIN_XHD_SPOKES = 4096
COURSE_SAMPLES = 16
BLOB_HISTORY_MAX = 0
GUARD_ZONES = 0
## NOTE: most of this information is from the froject openCPN radar plugin. LINK: https://github.com/opencpn-radar-pi/radar_pi
# largest packet seen so far from a Raymarine is 626
#SOURCE_IP = '172.16.2.0'
SOURCE_IP = '198.18.0.249' # check correct


class DisplayRadar:
    def __init__(self, steps):
        self.steps = steps
        self.grid = np.zeros((steps*2, steps*2))
        self.range = 0

    def add_spokes(self, spokes):
        for si, spoke in enumerate(spokes):
            angle = si/4
            #if 1 < angle < 90:
            spoke_leng = len(spoke)
            if spoke_leng > 0:
                bang_scale_array = np.frombuffer(spoke, dtype=np.uint8).astype(np.float32)/255
                bis_array = np.arange(0, spoke_leng).astype(np.float32)
                bis_array *= (self.steps/spoke_leng)
                X = np.cos(np.radians(angle-90.)) * bis_array
                X = np.rint(X).astype(np.uint16)
                X += self.steps-1

                Y = np.sin(np.radians(angle - 90.)) * bis_array
                Y = np.rint(Y).astype(np.uint16)
                Y += self.steps - 1

                for i in range(len(X)):
                    self.grid[Y[i]][X[i]] = bang_scale_array[i]

            # for bi, bang in enumerate(spoke):
            #     x = round(math.cos(math.radians(angle-90))*self.steps*(bi/spoke_leng))+self.steps-1
            #     y = round(math.sin(math.radians(angle-90))*self.steps*(bi/spoke_leng))+self.steps-1
            #     self.grid[y][x] = bang/255 # 255 is max


        # leng = len(line)
        # X = np.arange(0,leng)
        # Y = np.zeros(leng)
        # for i in range(leng):
        #     Y[i] = line[i]
        #
        # plt.plot(X, Y)
        # plt.show()


class LineHistory:
    def __init__(self):
        self.line = b''
        self.time = 0.
        self.lat = 0.
        self.lng = 0.



def create_ticks(range):
    nticks = 8
    # very unsure if the range is correct. need to verify
    rng_H = range//2
    xi = np.linspace(0, packet_length*2, nticks)
    xs = [str(round(x)) for x in list(np.linspace(-rng_H, rng_H, nticks))]

    yi = np.linspace(0, packet_length*2, nticks)
    ys = [str(round(x)) for x in list(np.linspace(-rng_H, rng_H, nticks))][::-1]
    return (xi, xs), (yi, ys)


if __name__ == "__main__":
    print("Dir:", os.getcwd())
    #log_path = "logs/garmin_xhd.pcap"
    log_path = "logs/quantum_1.pcap"
    # pkts = scu.rdpcap()
    #plen = len(pkts)
    #print("Packets:", plen)
    radar_data = QuantumData()
    M = 5000
    cpi = 0 # correct packet index
    #A = np.zeros(plen)
    packet_length = 731
    dr = DisplayRadar(packet_length)
    i = 0
    metadata = dict(title='Movie Test', artist='Matplotlib',
                comment='Movie support!')
    # writer = FFMpegWriter(fps=15, metadata=metadata)
    # fig = plt.figure()
    # with writer.saving(fig, "writer_test.mp4", 100):
    for (pkt_data, pkt_metadata,) in RawPcapReader(log_path):
        ether_pkt = Ether(pkt_data)
        good_packet = False
        if 'type' in ether_pkt.fields:
            if ether_pkt.type == 0x0800:
                ip_pkt = ether_pkt[IP]
                if ip_pkt.proto == 17:
                    if ip_pkt.src == SOURCE_IP:
                        if UDP in ether_pkt:
                            udp_pkt = ether_pkt[UDP]
                            #if udp_pkt.len >= 100:
                            good_packet = True

        if not good_packet:
            continue

        if good_packet:  ## TODO: check type!
            pkt = ether_pkt
            #print("Length:", pkt.wirelen)
            radar_data.update(pkt)

            # if radar_data.range_meters:
            #     (xi, xs), (yi, ys) = create_ticks(radar_data.range_meters)
            # if cpi % 1400 == 0:
            #     dr.add_spokes(radar_data.spokes)
            #     plt.imshow(dr.grid, cmap='plasma', interpolation='nearest')  # cmap hot plasma

            #     plt.xticks(xi, xs)
            #     plt.yticks(yi, ys)

            #     # adding vertical line in data co-ordinates
            #     plt.axvline(x=packet_length, alpha=0.3, c='white', ls='-')

            #     # adding horizontal line in data co-ordinates
            #     plt.axhline(y=packet_length, alpha=0.3, c='white', ls='-')

            #     plt.suptitle(f"Radar detections time: {datetime.utcfromtimestamp(int(radar_data.time)).strftime('%Y-%m-%d %H:%M:%S')}")
            #     plt.ylabel('AFT <--      (meters)   --> STERN')
            #     plt.xlabel('PORT <--       (meters) --> STARBOARD')
            #     writer.grab_frame()
            #     #plt.savefig(f'images/radar_{cpi}.png')
            #     print(f"created map for cpi {cpi}")


            # #xhd_D.print_stat()
            # #Y[cpi] = math.cos(xhd_D.angle*(math.pi/180))
            # #A[cpi] = xhd_D.angle
            # cpi += 1
        dr.range = radar_data.range_meters



    # X = np.arange(0, plen)
    # #plt.plot(X, A)
    # plt.plot(X, B)
    # plt.plot(X, C)
    # plt.plot(X, D)
    # plt.ylabel("Degrees")
    # plt.xlabel("Frame Number")
    # plt.show()