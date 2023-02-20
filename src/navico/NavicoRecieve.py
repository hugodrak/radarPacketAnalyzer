from src.RadarInfo import RadarInfo
from src.tools import form_byte
from src.plotter import Plotter
import dpkt
import math
import logging
from src.tools import good_hex

SPOKES = 4096
NAVICO_SPOKES_RAW = 4096
NAVICO_SPOKES = 2048
NAVICO_SPOKE_LEN = 1024
GUARD_ZONES = 0
ignore_radar_heading = False
CORRECT_HEADER = b'\x01\x00\x00\x00\x00 \x00\x02'
IS_HALO = False
"""
 Heading on radar. Observed in field:
 - Hakan: BR24, no RI: 0x9234 = negative, with recognisable 1234 in hex?
 - Marcus: 3G, RI, true heading: 0x45be
 - Kees: 4G, RI, mag heading: 0x07d6 = 2006 = 176,6 deg
 - Kees: 4G, RI, no heading: 0x8000 = -1 = negative
 - Kees: Halo, true heading: 0x4xxx => true
 Known values for heading value:
"""
HEADING_TRUE_FLAG = 0x4000
HEADING_MASK = NAVICO_SPOKES_RAW - 1
DEGREES_PER_ROTATION = 360
LOOKUP_NIBBLE_TO_BYTE = [0, 0x32, 0x40, 0x4e, 0x5c, 0x6a, 0x78, 0x86, 0x94, 0xa2, 0xb0, 0xbe, 0xcc, 0xda, 0xe8, 0xf4]
LOOKUP_SPOKE = {"LOW_NORMAL": 0, "LOW_BOTH": 1, "LOW_APPROACHING": 2, "HIGH_NORMAL": 3, "HIGH_BOTH": 4, "HIGH_APPROACHING": 5}


def scale_raw_to_degrees(raw):
    return raw * DEGREES_PER_ROTATION / NAVICO_SPOKES_RAW


def scale_degrees_to_raw(angle):
    return int(angle*NAVICO_SPOKES_RAW/DEGREES_PER_ROTATION)


def mod_degrees_float(angle):
    return math.fmod(angle + 2*DEGREES_PER_ROTATION, DEGREES_PER_ROTATION)


def mod_spokes(raw):
    return (raw + 2 * SPOKES) % SPOKES


def heading_valid(raw):
    return (raw & ~(HEADING_TRUE_FLAG | HEADING_MASK)) == 0


class NavicoFrame:
    def __init__(self, fid):
        self.id = fid
        self.raw_data = bytearray()
        self.data = []  # (header, spoke)
        self._prev_header = None

    def add_main(self, data):
        self.raw_data.extend(data)
        # for di in range(0, len(data), 536):
        #     d = data[di:di + 536]
        #     header_len = form_byte(d, 0)
        #     h = d[:header_len]  # header
        #     if not (h[-1] == 0x80 or h[-1] == 0xa0):
        #         logging.warning(f"Frame {self.id} contains non correct header, skipping")
        #         continue
        #     hits = d[header_len:]
        #     self.data.append([h, hits])

    def add_buffer(self, buff_data):
        # need to check offset
        # for offset, spoke in buff_data:
        #     self.raw_data[offset:offset+len(raw_data)] = raw_data
        #
        # h=0
        for raw_data in buff_data:
            self.raw_data.extend(raw_data)


        # rest_i = 512 - len(self.data[-1][1])
        # rest = raw_data[:rest_i]
        # self.data[-1][1] = self.data[-1][1] + rest
        # if len(self.data[-1][1]) != 512:
        #     logging.warning(f"Line not complete for id {self.id}")
        # data = raw_data[rest_i:]
        #
        for di in range(0, len(self.raw_data), 536):
            d = self.raw_data[di:di + 536]
            header_len = form_byte(d, 0)
            h = d[:header_len]  # header
            if not (h[-1] == 0x80 or h[-1] == 0xa0):
                logging.warning(f"Frame {self.id} contains non correct header, skipping")
                continue
            hits = d[header_len:]
            self.data.append([h, hits])

    def total(self):
        for header, spoke in self.data:
            self.raw_data.extend(header)
            self.raw_data.extend(spoke)

        print(good_hex(self.raw_data))

    def frame_complete(self):
        good = True
        if len(self.data) != 32:
            good = False
        for heading, spoke in self.data:
            if len(heading) != 24:
                good = False
            if len(spoke) != 512:
                good = False

        return good



class NavicoData:
    def __init__(self):
        self.ri = RadarInfo(NAVICO_SPOKES)
        self.packet_length = 0
        self.offset = 42
        self.time = 0
        self.packet_type = 0
        self.scan_length = 0
        self.range_meters = 0
        self.display_meters = 0
        self.scan_length_bytes_s = 0
        self.scan_length_bytes_i = 0
        self.spoke_index = 0

        ## --------- Angle stuff ------
        self.angle_raw = 0
        self.angle_deg = .0
        self.spokes = 0
        self.next_spoke = 0
        self.missing_spokes = 0
        self.heading = 0.
        self.bearing_raw = 0.
        self.heading_raw = 0.  # this is something we need to get from the gps
        # --- data---
        self.line_data = None
        self.raw_packet_load = None
        self.spokes = [0]*4096
        self.lookup_data = [[0]*256]*6  # TODO: continue here
        self.initialize_lookup_data()

    def initialize_lookup_data(self):
        if self.lookup_data[2][255] == 0:
            for j in range(255):
                low = LOOKUP_NIBBLE_TO_BYTE[j & 0x0f]
                high = LOOKUP_NIBBLE_TO_BYTE[(j & 0x0f) >> 4]
                self.lookup_data[LOOKUP_SPOKE["LOW_NORMAL"]][j] = low
                self.lookup_data[LOOKUP_SPOKE["HIGH_NORMAL"]][j] = high
                match low:
                    case 0xf4:
                        self.lookup_data[LOOKUP_SPOKE["LOW_BOTH"]][j] = 0xff
                        self.lookup_data[LOOKUP_SPOKE["LOW_APPROACHING"]][j] = 0xff

                    case 0xe8:
                        self.lookup_data[LOOKUP_SPOKE["LOW_BOTH"]][j] = 0xfe
                        self.lookup_data[LOOKUP_SPOKE["LOW_APPROACHING"]][j] = low

                    case _:
                        self.lookup_data[LOOKUP_SPOKE["LOW_BOTH"]][j] = low
                        self.lookup_data[LOOKUP_SPOKE["LOW_APPROACHING"]][j] = low

                match high:
                    case 0xf4:
                        self.lookup_data[LOOKUP_SPOKE["HIGH_BOTH"]][j] = 0xff
                        self.lookup_data[LOOKUP_SPOKE["HIGH_APPROACHING"]][j] = 0xff

                    case 0xe8:
                        self.lookup_data[LOOKUP_SPOKE["HIGH_BOTH"]][j] = 0xfe
                        self.lookup_data[LOOKUP_SPOKE["HIGH_APPROACHING"]][j] = high

                    case _:
                        self.lookup_data[LOOKUP_SPOKE["HIGH_BOTH"]][j] = high
                        self.lookup_data[LOOKUP_SPOKE["HIGH_APPROACHING"]][j] = high

    def add_spoke(self):
        spoke = self.spoke_index
        self.ri.m_spokes += 1
        if self.next_spoke >= 0 and spoke != self.next_spoke:
            if spoke > self.next_spoke:
                self.ri.m_missing_spokes += spoke - self.next_spoke
            else:
                self.ri.m_missing_spokes += SPOKES + spoke - self.next_spoke

        self.next_spoke = (spoke + 1) % SPOKES
        self.bearing_raw = self.heading_raw + self.angle_raw
        a = mod_spokes(self.angle_raw//2)
        b = mod_spokes(self.bearing_raw//2)
        #length = NAVICO_SPOKE_LEN
        # data_highres = [0]*NAVICO_SPOKE_LEN
        # doppler = self.ri.m_doppler
        # # doppler filter
        # if doppler < 0 or doppler > 2:
        #     doppler = 0
        #
        # lookup_low = self.lookup_data[LOOKUP_SPOKE["LOW_NORMAL"] + doppler]
        # lookup_high = self.lookup_data[LOOKUP_SPOKE["HIGH_NORMAL"] + doppler]
        # for i in range(NAVICO_SPOKE_LEN//2):
        #     data_highres[2*i] = lookup_low[self.line_data[i]]  # What does this do?
        #     data_highres[2*i+1] = lookup_high[self.line_data[i]]

        self.ri.process_radar_spokes(a, b, self.line_data, 512, self.range_meters, self.time)

    def update(self, ts, header, spoke):
        """
        struct br4g_header {
          uint8_t headerLen;       // 1 bytes
          uint8_t status;          // 1 bytes
          uint8_t scan_number[2];  // 2 bytes, 0-4095
          uint8_t u00[2];          // Always 0x4400 (integer)
          uint8_t largerange[2];   // 2 bytes or -1
          uint8_t angle[2];        // 2 bytes
          uint8_t heading[2];      // 2 bytes heading with RI-10/11 or -1. See bitmask explanation above.
          uint8_t smallrange[2];   // 2 bytes or -1
          uint8_t rotation[2];     // 2 bytes, rotation/angle
          uint8_t u02[4];          // 4 bytes signed integer, always -1
          uint8_t u03[4];          // 4 bytes signed integer, mostly -1 (0x80 in last byte) or 0xa0 in last byte
        };                         /* total size = 24 */
        """

        header_len = form_byte(header, 0)
        if header_len != 24 and len(header) != 24:
            raise ValueError("Incorrect header!")

        self.packet_length = len(spoke)

        self.spoke_index = form_byte(header, 2, 3)  # scan num
        self.angle_raw = form_byte(header, 8, 9)
        self.angle_deg = float(self.angle_raw)/4094 * 360.0  # angle 0 -> 4094
        self.heading_raw = form_byte(header, 10, 11)
        radar_heading_valid = heading_valid(self.heading_raw)
        radar_heading_true = (self.heading_raw & HEADING_TRUE_FLAG) != 0
        if radar_heading_valid and not ignore_radar_heading:
            if not IS_HALO:  # TODO: check this
                self.heading = mod_degrees_float(scale_raw_to_degrees(self.heading_raw))
        else:
            pass
            # TODO: get heading

        #self.heading = self.heading_raw/65535 * 360. #?
        self.line_data = spoke
        if self.spoke_index > 4095 or self.spoke_index < 0:
            h=0
        #print(self.spoke_index)
        self.spokes[self.spoke_index] = self.line_data
        large_range = form_byte(header, 6, 7)
        small_range = form_byte(header, 12, 13)
        if large_range == 0x80:
            if small_range == 0xffff:
                self.range_meters = 0  # Invalid range received
            else:
                self.range_meters = small_range / 4
        else:
            self.range_meters = large_range * small_range / 512
        self.time = ts
        self.add_spoke()

    def print_stat(self):
        print(self.angle_deg)

    def complete_spokes(self):
        if self.ri.m_missing_spokes == 0:
            return True
        return False

    def to_plotter(self):
        return self.ri.to_plotter()


def main(fname):
    plott = Plotter("Halo 24")
    ND = NavicoData()
    UDP_IP = "localhost"
    UDP_PORT = 2368
    SOURCE_IP = '192.168.1.120'  # check correct
    MIN_LEN = 1400
    spokes_per_packet = 32
    # handle part byte packets before or after udp main packet.
    more_fragments = 0
    with open(fname, "rb") as f:
        pcap = dpkt.pcap.Reader(f)
        data = bytearray()
        fragment_count = 0
        buffer = {}
        frame = None
        for ts, buf in pcap:
            eth = dpkt.ethernet.Ethernet(buf)
            if eth.type == dpkt.ethernet.ETH_TYPE_IP:
                ip = eth.data
                # TODO: check id match
                h=0
                if ip.p == dpkt.ip.IP_PROTO_UDP:
                    ip_src_str = ".".join([str(int(x)) for x in ip.src])
                    if ip_src_str == SOURCE_IP:
                        h=0
                        if type(ip.data) == dpkt.udp.UDP:
                            udp = ip.data
                            if len(udp.data) > MIN_LEN:
                                frame = NavicoFrame(ip.id)
                                if udp.data[:8] != CORRECT_HEADER:
                                    logging.warning(f'Frame with id {ip.id} has incorrect header! Skipping!')
                                    continue

                                frame.add_main(udp.data[8:])

                        elif type(ip.data) == bytes:
                            if len(buffer.keys()) > 4:
                                raise ValueError("Buffer overfilling!!")
                            buffer.setdefault(ip.id, [])
                            if len(ip.data) > 0:
                                buffer[ip.id].append(ip.data)
                            if len(buffer[ip.id]) == 11:
                                frame.add_buffer(buffer[ip.id])
                                h=0
                                if frame.frame_complete():
                                    #print(ip.id)
                                    del buffer[ip.id]
                                    for header, spoke in frame.data:
                                        ND.update(ts, header, spoke)

                                    #if ND.complete_spokes():# and 0 < ND.spoke_index < 100:
                                    plott.update(ND.to_plotter())



                # if more_fragments:
                #     if type(ip.data) == bytes:
                #         if fragment_count >= 10:
                #             more_fragments = 0
                #             fragment_count = 0
                #             data.extend(ip.data)
                #         else:
                #             more_fragments = ip.mf
                #             fragment_count += 1
                #             data.extend(ip.data)
                #             continue
                #
                # if ip.p == dpkt.ip.IP_PROTO_UDP:
                #     udp = ip.data
                #     ip_src_str = ".".join([str(int(x)) for x in ip.src])
                #     if ip.id == 62451:
                #         g=0
                #     if type(udp) == dpkt.udp.UDP:
                #         velodata = udp.data
                #
                #         if ip_src_str == SOURCE_IP:
                #             if len(velodata) > MIN_LEN:
                #                 more_fragments = ip.mf
                #                 data.extend(velodata[8:])
                #     elif len(data) > 0:
                #         if len(data) > 18000:
                #             h = 0
                #         ND.update(data, ts)
                #         if ND.spoke_zero():
                #             plott.update(ND.to_plotter())
                #         data = bytearray()


if __name__ == "__main__":
    main("../../eenx_logs/goodlog2.pcap")
