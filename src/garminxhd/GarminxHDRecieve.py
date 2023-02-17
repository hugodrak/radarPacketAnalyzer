import RadarInfo

SPOKES = 1440

GUARD_ZONES = 0


def mod_spokes(raw):
    return (raw + 2 * SPOKES) % SPOKES


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
        """
        struct radar_line {
            uint32_t packet_type; // const at 98 09 00 00 (2456)
            uint32_t len1;        // const at d3 02 00 00 (723)
            uint16_t fill_1;      // const at 01 00 (1)
            uint16_t scan_length; // const at d3 02  (723)
            uint16_t angle;       // var 00 00 -> F8 2C, IS little endian. (((2c f8)/8)*0.25=360)
            uint16_t fill_2;      // const at 00 00 (0)
            uint32_t range_meters;// const at 78 0e 00 00    (3704)
            uint32_t display_meters;// const at 47 10 00 00 (4167)
            uint16_t fill_3;       // const at 00 00  (0)
            uint16_t scan_length_bytes_s;  // const at b7 02,(695) Number of video bytes in the packet, Short
            uint16_t fills_4;      // const at 08 01 (264)
            uint32_t scan_length_bytes_i;  // const at b7 02 00 00,(695) Number of video bytes in the packet, Integer
            uint16_t fills_5;      // const at 00 00 (0)
            uint8_t line_data[GARMIN_XHD_MAX_SPOKE_LEN];
            };
        """
        ## TODO: convert to struct with scapy
        self.packet_length = packet.len
        self.time = packet.time
        self.raw_packet_load = packet.original
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
