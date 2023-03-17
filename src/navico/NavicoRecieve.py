import os
import sys
from src.RadarInfo import RadarInfo
from src.navico.NavicoControl import NavicoControl
import signal
import struct
import time

from scapy.all import sniff, UDP, Ether, IP, get_if_list
print(os.getcwd())
import logging

logging.getLogger().setLevel(logging.INFO)
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

    def __init__(self):
        self.ri = RadarInfo(NAVICO_SPOKES)
        self.nControl = NavicoControl()
        self.do_receive = True

    def process_report(self, report):
        #logging.info("processing")

        #self.ri.reset_timeout(time.time()) # TODO: implement
        if report[1] == 0xc4:
            # looks like a radar report, is it?
            report_len = len(report)
            #print(report_len)
            if report_len == 18 and report[0] == 0x01: # length 18, 01 C4, most common
                logging.info("18 01 c4")
                s = get_vars(self.RadarReport_01C4_18, report)
                self.ri.m_radar_status = s[2]
                match self.ri.m_radar_status:
                    case 0x01:
                        self.ri.m_state = "RADAR STANDBY"
                    case 0x02:
                        self.ri.m_state = "RADAR TRANSMIT"
                    case 0x05:
                        self.ri.m_state = "RADAR SPINNING UP"
                    case _:
                        self.ri.m_state = "UNKNOWN"

                #logging.info(f"RadarInfo State change to: {self.ri.m_state}")

            elif report_len == 99 and report[0] == 0x02: #length 99, 02 C4
                logging.info("99 02 c4")
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
                logging.info("129 03 c4")
                logging.info("radar type message. Not implemented")

            elif report_len == 66 and report[0] == 0x04: # 66 bytes starting with 04 C4
                logging.info("66 04 c4")
                s = get_vars(self.RadarReport_04C4_66, report)
                self.ri.m_bearing_alignment = s[3]
                self.ri.m_antenna_height = s[5]
                self.ri.m_halo_light = s[10]

            elif report_len == 21 and report[0] == 0x08: # length 21, 08 C4 contains Doppler data in extra 3 bytes
                logging.info("21 08 c4")
                s = get_vars(self.RadarReport_08C4_21, report)
                self.ri.m_doppler_state = s[18]
                self.ri.m_doppler_speed = s[19]

            elif report_len == 18 and report[0] == 0x08: #length 18, 08 C4 contains scan speed, noise rejection and target_separation and sidelobe suppression
                logging.info("18 08 c4")
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

    def start(self):
        self.nControl.start()
        # time.sleep(2)
        self.nControl.set_halo_light(3)
        # time.sleep(2)
        # self.nControl.set_halo_light(0)
        # time.sleep(2)
        # self.nControl.set_halo_light(3)
        # time.sleep(2)

    def stop(self):
        logging.info("Stopping")
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

        signal.signal(signal.SIGINT, self.stop_handler)
        while self.do_receive:
            time.sleep(0.2)
            pkts = sniff(iface="en7", filter=f"udp and dst port {self.nControl.addresses.addrReportB.port}", count=1, timeout=1) # might be to slow
            for pkt in pkts:
                if pkt[Ether][IP].haslayer(UDP):
                    if pkt[Ether][IP].dst == self.nControl.addresses.addrReportB.addr: # might be
                        udp = pkt[Ether][IP][UDP]
                        if "load" in dir(udp.payload):
                            payload = udp.payload.load
                            self.process_report(payload)


if __name__ == "__main__":
    nr = NavicoReceive()
    nr.start()
    nr.nControl.RadarTxOn()
    nr.receive()

