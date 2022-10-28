from scapy import utils as scu
import os
import numpy as np
import matplotlib.pyplot as plt
import math
import logging
from datetime import datetime
## Garmin xHD has 1440 spokes of varying 519 - 705 bytes each
#define GARMIN_XHD_SPOKES 1440
#define GARMIN_XHD_MAX_SPOKE_LEN 705
GARMIN_XHD_SPOKES = 1440
COURSE_SAMPLES = 16
BLOB_HISTORY_MAX = 0
GUARD_ZONES = 0
## NOTE: most of this information is from the froject openCPN radar plugin. LINK: https://github.com/opencpn-radar-pi/radar_pi


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


class RadarInfo:
    def __init__(self):
        self.m_main_bang_size = 0
        self.m_threshold = 0
        self.m_radar_timeout = 0
        self.m_data_timeout = 0
        self.m_state = "RADAR_OFF"
        self.m_spokes = 0
        self.m_missing_spokes = 0
        self.m_range = 0
        self.m_range_adjustment = 0
        self.m_pixels_per_meter = 0.
        self.m_arpa = 0
        self.m_course_index = 0
        self.m_heading = 0.  # this is something we need to get from the gps
        self.m_course_log = np.zeros(COURSE_SAMPLES)
        self.m_course = 0.
        self.m_last_angle = 0.
        self.m_last_rotation_time = 0.
        self.m_rotation_period = 0
        self.m_threshold_red = 200
        self.m_doppler_count = 0

        self.m_history = [] # (line, time, pos)

    def process_radar_spokes(self, angle, bearing, line_data, length, range_meters, time_rec):
        self.sample_course(angle)
        self.calculate_rotation_speed(angle, time_rec)
        if range_meters == 0:
            raise ValueError("Error process_radar_spokes range is zero")  # logging

        for i in range(self.m_main_bang_size):
            line_data[i] = 0

        thresh = self.m_threshold
        if thresh > 0:
            thresh *= (255 - BLOB_HISTORY_MAX) / 100 + BLOB_HISTORY_MAX
            for i in range(length):
                if line_data[i] < thresh:
                    line_data[i] = 0

        ppm = (length / range_meters) * (1. - self.m_range_adjustment * 0.001)

        if self.m_pixels_per_meter != ppm:
            print(f"Detected spoke change rate from {self.m_pixels_per_meter} to {ppm} pixels/m, {range_meters}")
            self.m_pixels_per_meter = ppm
            self.m_history = []

        #orientation = 0 # implement self.get_orientation() 0=North
        ## -------- Start processing ---------
        #weakest_normal_blob = self.m_threshold_red
        #hist_data = self.m_history[bearing].line
        self.m_history[bearing].time = time_rec
        self.m_history[bearing].line = line_data

        # for radius in range(length):
        #     if line_data[radius] >= weakest_normal_blob:
        #         # and add 1 of above threshold and set the left 2 bits, used for ARPA
        #         hist_data[radius] = 192  # this is C0, 1100 0000
        #     if line_data[radius] == 255:
        #         # approaching doppler targets
        #         # and add 1 of above threshold and set the left 2 bits, used for ARPA
        #         hist_data[radius] = 0xE0  # this is  1110 0000, bit 3 indicates this is an approaching target
        #         self.m_doppler_count += 1

        ## TODO: implement guard zones

    def sample_course(self, angle):
        # Calculates the moving average of m_hdt and returns this in m_course
        # This is a bit more complicated then expected, average of 359 and 1 is 180 and that is not what we want
        if (angle and 127) == 0:
            if self.m_course_log[self.m_course_index] > 720.:
                for i in range(0, COURSE_SAMPLES):
                    self.m_course_log[i] -= 720.
            if self.m_course_log[self.m_course_index] < -720.:
                for i in range(0, COURSE_SAMPLES):
                    self.m_course_log[i] += 720.
            hdt = self.m_heading

            while self.m_course_log[self.m_course_index] - hdt > 180.:
                hdt += 360.

            while self.m_course_log[self.m_course_index] - hdt < -180.:
                hdt -= 360.

            self.m_course_index += 1
            if self.m_course_index >= COURSE_SAMPLES:
                self.m_course_index = 0

            self.m_course_log[self.m_course_index] = hdt
            summ = 0
            for i in range(0, COURSE_SAMPLES):
                summ += self.m_course_log[i]

            self.m_course = math.fmod(summ/COURSE_SAMPLES + 720., 360)

    def calculate_rotation_speed(self, angle, time_rec):
        if angle < self.m_last_angle:
            if self.m_last_rotation_time != 0 and time_rec > self.m_last_rotation_time + 100:
                delta = time_rec - self.m_last_rotation_time
                self.m_rotation_period = int(delta)
            self.m_last_rotation_time = time_rec
        self.m_last_angle = angle


def mod_spokes(raw):
    return (raw + 2 * GARMIN_XHD_SPOKES) % GARMIN_XHD_SPOKES


class XHDData:
    def __init__(self):
        self.ri = RadarInfo()
        self.packet_length = 0
        self.offset = 42
        self.time = 0
        self.packet_type = 0
        self.scan_length = 0
        self.range_meters = 0
        self.display_meters = 0
        self.scan_length_bytes_s = 0
        self.scan_length_bytes_i = 0

        ## --------- Angle stuff ------
        self.angle_raw = 0
        self.angle_deg = .0
        self.spokes = 0
        self.next_spoke = 0
        self.missing_spokes = 0
        self.bearing_raw = 0.
        self.heading_raw = 0.  # this is something we need to get from the gps
        # --- data---
        self.line_data = None
        self.raw_packet_load = None
        self.spokes = [b'']*1440

    def add_spoke(self):
        spoke = self.angle_raw
        self.ri.m_spokes += 1
        if self.next_spoke >= 0 and spoke != self.next_spoke:
            if spoke > self.next_spoke:
                self.ri.m_missing_spokes += spoke - self.next_spoke
            else:
                self.ri.m_missing_spokes += GARMIN_XHD_SPOKES + spoke - self.next_spoke

        self.next_spoke = (spoke + 1) % GARMIN_XHD_SPOKES
        self.bearing_raw = self.heading_raw + self.angle_raw
        a = mod_spokes(self.angle_raw)
        b = mod_spokes(self.bearing_raw)
        leng = self.packet_length - self.offset
        # lower_leng = leng//5
        # X = np.arange(0, lower_leng)
        # Y = np.zeros(lower_leng)
        # for radius in range(lower_leng):
        #     Y[radius] = self.line_data[radius] ## plot avgs instead
        # plt.plot(X, Y)
        # plt.xticks(np.linspace(0, lower_leng, 10), [int(x) for x in np.linspace(0, self.range_meters//5, 10)])
        # plt.show()
        self.ri.process_radar_spokes(a, b, self.line_data, leng, self.display_meters, self.time)

    def form_byte(self, start, end, little=True, signed=False):
        start += self.offset
        end += self.offset
        out = 0
        shift = 0 if little else 8*(end-start)
        try:
            for i in range(start, end + 1):
                out += self.raw_packet_load[i] << shift
                if little:
                    shift += 8
                else:
                    shift -= 8
            return out
        except:
            print(self.packet_length)
            raise ValueError(f"Index")

    def update(self, packet):
        ## TODO: convert to struct with scapy
        self.packet_length = packet.wirelen
        self.time = packet.time
        self.raw_packet_load = packet.load
        self.packet_type = self.form_byte(0, 3)  # const
        self.scan_length = self.form_byte(10, 11)  # const
        self.spoke_index = self.form_byte(12, 13) // 8  # so the structure is: 1440 spokes per revolution, each spoke matches 1/4 degree, the input int is divided by 8 to give spoke index
        self.angle_deg = self.spoke_index * (1/4)
        self.range_meters = self.form_byte(16, 19)  # const
        self.display_meters = self.form_byte(20, 23)  # const
        self.scan_length_bytes_s = self.form_byte(26, 27)  # const
        self.scan_length_bytes_i = self.form_byte(30, 33)  # const
        self.line_data = self.raw_packet_load[self.offset:]
        self.spokes[self.spoke_index] = self.line_data

        #self.add_spoke()
        # 36->

    def print_stat(self):
        print(self.angle_deg)


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
    pkts = scu.rdpcap("logs/garmin_xhd.pcap")
    plen = len(pkts)
    print("Packets:", plen)
    xhd_D = XHDData()
    M = 5000
    cpi = 0 # correct packet index
    #A = np.zeros(plen)
    packet_length = 731
    dr = DisplayRadar(packet_length)

    for i, pkt in enumerate(pkts):
        if i >= M:
            print(i)
            break
        if pkt.wirelen >= 505:  ## TODO: check type!
            #print("Length:", pkt.wirelen)
            xhd_D.update(pkt)
            if xhd_D.range_meters:
                (xi, xs), (yi, ys) = create_ticks(xhd_D.range_meters)
            if cpi % 1400 == 0:
                dr.add_spokes(xhd_D.spokes)
                plt.imshow(dr.grid, cmap='plasma', interpolation='nearest')  # cmap hot plasma

                plt.xticks(xi, xs)
                plt.yticks(yi, ys)

                # adding vertical line in data co-ordinates
                plt.axvline(x=packet_length, alpha=0.3, c='white', ls='-')

                # adding horizontal line in data co-ordinates
                plt.axhline(y=packet_length, alpha=0.3, c='white', ls='-')

                plt.suptitle(f"Radar detections time: {datetime.utcfromtimestamp(int(xhd_D.time)).strftime('%Y-%m-%d %H:%M:%S')}")
                plt.ylabel('AFT <--      (meters)   --> STERN')
                plt.xlabel('PORT <--       (meters) --> STARBOARD')
                plt.savefig(f'images/radar_{cpi}.png')
                print(f"created map for cpi {cpi}")


            #xhd_D.print_stat()
            #Y[cpi] = math.cos(xhd_D.angle*(math.pi/180))
            #A[cpi] = xhd_D.angle
            cpi += 1
        dr.range = xhd_D.range_meters



    # X = np.arange(0, plen)
    # #plt.plot(X, A)
    # plt.plot(X, B)
    # plt.plot(X, C)
    # plt.plot(X, D)
    # plt.ylabel("Degrees")
    # plt.xlabel("Frame Number")
    # plt.show()