import os
import sys
import threading

from src.RadarInfo import RadarInfo
from src.navico_playback.NavicoControl import NavicoControl
from src.tools import form_byte
import signal
import struct
import time
import queue
import numpy as np

from scapy.all import sniff, UDP, Ether, IP, get_if_list
import logging

#logging.getLogger().setLevel(logging.INFO)
logging.getLogger().setLevel(logging.CRITICAL)
NAVICO_SPOKES = 2048


def get_vars(format, data):
    unpacked = struct.unpack(format, data)
    return [x[0] if type(x) == bytes else x for x in unpacked]


class NavicoReceive:
    RadarReport_01C4_18 = "<ssssssHHHssssss"
    RadarReport_02C4_99 = "<ssIssIsssHIsssIIsssssssssssIIIIIIIIIIIIII"
    RadarReport_04C4_66 = "<ssIHHHIssssIIIIIIIIIIIH"
    RadarReport_08C4_21 = "<ssssssssssHsssssssH"
    RadarReport_08C4_18 = "<ssssssssssHssssss"
    #br4g_header = "<ssssssssssssssssssssssss"
    br4g_header = "<ssHHHHHHHII"

    def __init__(self):
        self.interface = "en0"
        self.logfile = "eenx_logs/startup_doppler_opencpn.pcap"
        out_path = os.path.join("output/", os.path.basename(os.path.splitext(self.logfile)[0])+".csv")
        self.output = open(out_path, "w")
        self.output.write("time,bearing,spoke_index,range,lat,long,0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,71,72,73,74,75,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94,95,96,97,98,99,100,101,102,103,104,105,106,107,108,109,110,111,112,113,114,115,116,117,118,119,120,121,122,123,124,125,126,127,128,129,130,131,132,133,134,135,136,137,138,139,140,141,142,143,144,145,146,147,148,149,150,151,152,153,154,155,156,157,158,159,160,161,162,163,164,165,166,167,168,169,170,171,172,173,174,175,176,177,178,179,180,181,182,183,184,185,186,187,188,189,190,191,192,193,194,195,196,197,198,199,200,201,202,203,204,205,206,207,208,209,210,211,212,213,214,215,216,217,218,219,220,221,222,223,224,225,226,227,228,229,230,231,232,233,234,235,236,237,238,239,240,241,242,243,244,245,246,247,248,249,250,251,252,253,254,255,256,257,258,259,260,261,262,263,264,265,266,267,268,269,270,271,272,273,274,275,276,277,278,279,280,281,282,283,284,285,286,287,288,289,290,291,292,293,294,295,296,297,298,299,300,301,302,303,304,305,306,307,308,309,310,311,312,313,314,315,316,317,318,319,320,321,322,323,324,325,326,327,328,329,330,331,332,333,334,335,336,337,338,339,340,341,342,343,344,345,346,347,348,349,350,351,352,353,354,355,356,357,358,359,360,361,362,363,364,365,366,367,368,369,370,371,372,373,374,375,376,377,378,379,380,381,382,383,384,385,386,387,388,389,390,391,392,393,394,395,396,397,398,399,400,401,402,403,404,405,406,407,408,409,410,411,412,413,414,415,416,417,418,419,420,421,422,423,424,425,426,427,428,429,430,431,432,433,434,435,436,437,438,439,440,441,442,443,444,445,446,447,448,449,450,451,452,453,454,455,456,457,458,459,460,461,462,463,464,465,466,467,468,469,470,471,472,473,474,475,476,477,478,479,480,481,482,483,484,485,486,487,488,489,490,491,492,493,494,495,496,497,498,499,500,501,502,503,504,505,506,507,508,509,510,511\n")
        self.ri = RadarInfo(NAVICO_SPOKES)
        self.nControl = NavicoControl(self.interface)
        self.do_receive = True
        self.spoke_log = None
        self.spokes_thread = None
        self.do_receive_spokes = None


    def process_report(self, report):
        #logging.info("processing")

        #self.ri.reset_timeout(time.time()) # TODO: implement
        if report[1] == 0xc4:
            # looks like a radar report, is it?
            report_len = len(report)
            logging.info(f"{report_len} {report[0]:02x} {report[1]:02x}")
            #print(report_len)
            if report_len == 18 and report[0] == 0x01: # length 18, 01 C4, most common
                #logging.info("18 01 c4")
                s = get_vars(self.RadarReport_01C4_18, report)

                self.ri.m_radar_status = s[2]
                if self.ri.m_radar_status == 0x01:
                    self.ri.m_state = "RADAR STANDBY"
                elif self.ri.m_radar_status == 0x02:
                    self.ri.m_state = "RADAR TRANSMIT"
                elif self.ri.m_radar_status == 0x05:
                    self.ri.m_state = "RADAR SPINNING UP"
                else:
                    self.ri.m_state = "UNKNOWN"


                #logging.info(f"RadarInfo State change to: {self.ri.m_state}")

            elif report_len == 99 and report[0] == 0x02: #length 99, 02 C4
                #logging.info("99 02 c4")
                s = get_vars(self.RadarReport_02C4_99, report)
                self.ri.m_gain = s[6]*100 / 255
                self.ri.m_rain = s[12]*100 / 255
                self.ri.m_sea = s[10]*100 / 255
                self.ri.m_mode = s[4]
                self.ri.m_target_boost = s[26]
                self.ri.m_interference_rejection = s[18]
                self.ri.m_target_expansion = s[22]
                self.ri.m_range = s[2]/10
                #logging.info(f"uppdated gain: {self.ri.m_gain}")

            elif report_len == 129 and report[0] == 0x03: # 129 bytes starting with 03 C4
                #logging.info("129 03 c4")
                logging.info("radar type message. Not implemented")

            elif report_len == 66 and report[0] == 0x04: # 66 bytes starting with 04 C4
                #logging.info("66 04 c4")
                s = get_vars(self.RadarReport_04C4_66, report)
                self.ri.m_bearing_alignment = s[3]
                self.ri.m_antenna_height = s[5]
                self.ri.m_halo_light = s[10]

            elif (report_len == 21 or report_len == 22)and report[0] == 0x08: # length 21, 08 C4 contains Doppler data in extra 3 bytes
                #logging.info("21 08 c4")
                if report_len == 22:
                    report = report[:-1]
                s = get_vars(self.RadarReport_08C4_21, report)
                self.ri.m_doppler_state = s[17]
                self.ri.m_doppler_speed = s[18]
                if self.ri.m_doppler_state != 0:
                    logging.warning(f"doppler State: {self.ri.m_doppler_state}")
                logging.info(f"radar doppler message. State: {self.ri.m_doppler_state}, Speed: {self.ri.m_doppler_speed}")

            elif report_len == 18 and report[0] == 0x08: #length 18, 08 C4 contains scan speed, noise rejection and target_separation and sidelobe suppression
                #logging.info("18 08 c4")
                s = get_vars(self.RadarReport_08C4_18, report)
                self.ri.m_sea_state = s[2]
                self.ri.m_local_interference_rejection = s[3]
                self.ri.m_scan_speed = s[4]
                self.ri.m_sls_auto = s[5]
                self.ri.m_side_lobe_suppression = s[9] * 100 / 255
                self.ri.m_noise_rejection = s[11]
                self.ri.m_target_sep = s[12]
                self.ri.m_sea_clutter = s[13]
                self.ri.m_auto_sea_clutter = s[14]

        elif report[0] == 0x11 and report[1] == 0xc6:
            logging.info(f"Received heartbeat at {round(time.time())}")
        # else:
        #     logging.info("received other packet")

    def process_spokes(self, pkt):
        now = time.time()
        if len(pkt) < 1472:  # TODO: check17160
            logging.warning(f"Too few spokes in packet, got {len(pkt)}")
            return

        # TODO: do we get split packets or 17000?
        spokes = []
        for di in range(0, len(pkt), 536):
            d = pkt[di:di + 536]
            h = d[8:24+8]

            s = get_vars(self.br4g_header, h)
            #logging.info(s)

            header_len = s[0]
            header_status = s[1]
            scan_number = s[2]
            largerange = s[4]
            angle = s[5]
            heading = s[6]
            smallrange = s[7]
            rotation = s[8]

            #range_meters = -1
            if largerange == 0x80:
                if smallrange == 0xffff:  # Not gonna work due to uint.. check
                    range_meters = 0
                else:
                    range_meters = smallrange / 4
            else:
                range_meters = largerange * smallrange / 512

            if len(d) != 536:
                logging.warning(f"Frame at: {int(now)} is non-complete, skipping")
                continue

            if header_len != 24:
                logging.warning(f"Frame at: {int(now)}  has non-complete HEADER, skipping")
                continue

            header_ending = h[-1]
            # validation for status, header and packet len
            if not (header_ending == 0x80 or header_ending == 0xa0):
                logging.warning(f"Frame at: {int(now)} contains non correct header-ENDING ({hex(header_ending)}), skipping")
                continue
            if not (header_status == 0x02 or header_status == 0x12):
                logging.warning(f"Frame at: {int(now)} has non correct STATUS, skipping")
                continue

            # TODO: handle doppler
            raw_hits = d[header_len:]
            hits = np.zeros(512, dtype=np.float32)
            # TODO: implement 512 dopplerspoke and send and log
            if self.ri.m_doppler_state == 1 or self.ri.m_doppler_state == 2:  # normal or approaching
                for i, h in enumerate(raw_hits):
                    low_d = (h & 0x0f)
                    high_d = ((h & 0xf0) >> 4)
                    if (low_d == 0xf or low_d == 0xe) and (high_d == 0xf or high_d == 0xe):
                        # This should be right but try live to change between mode 1 and 2 and see difference, else check radarpi code
                        if h == 0xff:
                            self.ri.m_doppler_spokes[scan_number][i] = 1
                            #print(f"{h:02x} {high_d:01x} {low_d:01x}")
                        elif h == 0xee:
                            self.ri.m_doppler_spokes[scan_number][i] = 2

                        hits[i] = 1.0
                    else:
                        self.ri.m_doppler_spokes[scan_number][i] = 0
                        hits[i] = round(h/255, 5)
            else:
                for i, h in enumerate(raw_hits):
                    hits[i] = round(h/255, 5)

            if len(hits) != 512:
                logging.warning(f"Frame at: {int(now)} has non-complete spokes, skipping")
                continue

            # TODO: do not send heading due to lack of GPS.
            # TODO: check and implement doppler speed and doppler state!
            spokes.append({"time": round(now, 6), "range_meters": range_meters, "spoke_index": scan_number,
                           "angle": angle, "rotation": rotation, "spoke": hits})

        if len(spokes) != 2:  # 32
            logging.warning(f"spokes at {int(now)} not complete, only got {len(spokes)}")

        self.write_spoke_to_csv(spokes)  # TODO: publish

    def write_spoke_to_csv(self, spokes):
        # time,bearing,spoke_index,range,lat,long,
        for s in spokes:
            self.output.write(f'{s["time"]},{int(s["angle"])},{int(s["spoke_index"])},{round(s["range_meters"], 2)},0.0,0.0,{",".join([str(round(int(x)/255, 5)) for x in s["spoke"]])}\n')

    def start(self):
        self.nControl.start(self.logfile)
        # time.sleep(2)
        # nr.nControl.RadarTxOn()
        # self.nControl.set_halo_light(3)
        # nr.start_spokes()
        # time.sleep(2)
        # self.nControl.set_halo_light(0)
        # time.sleep(2)
        # self.nControl.set_halo_light(3)
        # time.sleep(2)

    def receive_spokes(self):
        logging.info("Start log spokes")

        while self.do_receive_spokes:
            #time.sleep(0.2)  # TODO: evaluate sleep time to get all!
            pkts = sniff(iface=self.interface, filter=f"udp and dst port {self.nControl.addresses.addrDataB.port} and dst host {self.nControl.addresses.addrDataB.addr}", count=1, timeout=1) # might be to slow
            for pkt in pkts:
                if pkt[Ether][IP].haslayer(UDP):
                    if pkt[Ether][IP].dst == self.nControl.addresses.addrDataB.addr:
                        udp = pkt[Ether][IP][UDP]
                        if "load" in dir(udp.payload):
                            payload = udp.payload.load
                            self.process_spokes(payload)

    def start_spokes(self):
        self.do_receive_spokes = True
        self.spokes_thread = threading.Thread(target=self.receive_spokes)
        self.spokes_thread.start()

    def stop_spokes(self):
        self.do_receive_spokes = False
        self.spokes_thread.join()

    def stop(self):
        logging.info("Stopping")
        self.stop_spokes()
        self.nControl.set_halo_light(0)
        self.nControl.RadarTxOff()
        self.nControl.stop()
        logging.info("Stopped, goodnight")

    def stop_handler(self, signum, frame):
        self.do_receive = False
        self.stop()

    def receive(self):
        logging.info("Start receive")
        logging.info(self.nControl.addresses.__dict__)

        #signal.signal(signal.SIGINT, self.stop_handler)

        # ctrl: dst port {self.nControl.addresses.addrReportB.port}
        # spokes: dst port {self.nControl.addresses.addrDataB.port} and dst host {self.nControl.addresses.addrDataB.addr}

        pkts = sniff(offline=self.logfile, filter="udp")  # might be to slow
        logging.info(f"{len(pkts)} packets")
        for pkt in pkts:
            if pkt[Ether][IP].haslayer(UDP):
                udp = pkt[Ether][IP][UDP]
                if "load" in dir(udp.payload):
                    payload = udp.payload.load
                    if pkt[Ether][IP].dst == self.nControl.addresses.addrReportB.addr and pkt[Ether][IP][UDP].dport == self.nControl.addresses.addrReportB.port: # might be
                        # control packets
                        self.process_report(payload)
                    elif pkt[Ether][IP].dst == self.nControl.addresses.addrDataB.addr and pkt[Ether][IP][UDP].dport == self.nControl.addresses.addrDataB.port:
                        # spoke packets
                        self.process_spokes(payload)


if __name__ == "__main__":
    nr = NavicoReceive()
    nr.start()

    #nr.nControl.set_doppler(1)

    nr.receive()


