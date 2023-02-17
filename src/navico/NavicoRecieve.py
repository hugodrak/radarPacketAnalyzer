from src.RadarInfo import RadarInfo
from src.tools import form_byte
import dpkt
SPOKES = 4096
GUARD_ZONES = 0
HEADING_TRUE_FLAG = 0x4000
HEADING_MASK = SPOKES - 1


def mod_spokes(raw):
    return (raw + 2 * SPOKES) % SPOKES


class NavicoData:
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
        self.spokes = [0]*4095

    def add_spoke(self):
        spoke = self.spoke_index
        self.ri.m_spokes += 1
        if 0 <= self.next_spoke != spoke:
            if spoke > self.next_spoke:
                self.ri.m_missing_spokes += spoke - self.next_spoke
            else:
                self.ri.m_missing_spokes += SPOKES + spoke - self.next_spoke

        self.next_spoke = (spoke + 1) % SPOKES
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
        self.ri.process_radar_spokes(a, b, self.line_data, leng, self.range_meters, self.time)

    def update(self, packet, ts):
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
        for di in range(0, len(packet), 536):
            d = packet[di:di + 536]
            header_len = form_byte(d, 0)
            h = d[:header_len]  # header
            hits = d[header_len:]
            self.packet_length = len(hits)
            self.spoke_index = form_byte(h, 2, 3)  # scan num
            self.angle_raw = form_byte(h, 8, 9)
            self.angle_deg = float(self.angle_raw)/4094 * 360.0  # angle 0 -> 4094
            self.heading_raw = form_byte(h, 10, 11)
            self.heading = self.heading_raw/65535 * 360. #?
            self.line_data = hits
            self.spokes[self.spoke_index] = self.line_data
            large_range = form_byte(h, 6, 7)
            small_range = form_byte(h, 12, 13)
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


def main(fname):
    ND = NavicoData()
    UDP_IP = "localhost"
    UDP_PORT = 2368
    SOURCE_IP = '192.168.1.120'  # check correct
    MIN_LEN = 1400
    spokes_per_packet = 32

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

                                data.extend(velodata[8:])
                    elif len(data) > 0:
                        ND.update(data, ts)
                        data = bytearray()


if __name__ == "__main__":
    main("../../eenx_logs/goodlog2.pcap")
