import os
import sys
import threading

from src.RadarInfo import RadarInfo
from src.navico.NavicoControl import NavicoControl
from src.tools import form_byte
import signal
import struct
import time
import queue

from scapy.all import sniff, UDP, Ether, IP, get_if_list
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
    #br4g_header = "<ssssssssssssssssssssssss"
    br4g_header = "<ssHHHHHHHII"

    def __init__(self):
        self.ri = RadarInfo(NAVICO_SPOKES)
        self.nControl = NavicoControl()
        self.do_receive = True
        self.spoke_log = None
        self.spokes_thread = None
        self.do_receive_spokes = None
        self.interface = "en7"

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
                self.ri.m_doppler_state = s[17]
                self.ri.m_doppler_speed = s[18]
                logging.info(f"radar doppler message. State: {self.ri.m_doppler_state}, Speed: {self.ri.m_doppler_speed}")

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

    def process_spokes(self, pkt):
        now = time.time()
        if len(pkt) < 17160:  # TODO: check
            logging.warning("Too few spokes in packet")
            return

        # TODO: do we get split packets or 17000?
        spokes = []
        for di in range(0, len(pkt), 536):
            d = pkt[di:di + 536]
            h = d[:24]
            s = get_vars(self.br4g_header, h)

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
                logging.warning(f"Frame with Id: {self.id} is non-complete, skipping")
                continue

            if header_len != 24:
                logging.warning(f"Frame with Id: {self.id} has non-complete HEADER, skipping")
                continue

            header_ending = h[-1]
            # validation for status, header and packet len
            if not (header_ending == 0x80 or header_ending == 0xa0):
                logging.warning(f"Frame at: {int(now)} contains non correct header-ENDING ({hex(header_ending)}), skipping")
                continue
            if not (header_status == 0x02 or header_status == 0x12):
                logging.warning(f"Frame at: {int(now)} has non correct STATUS, skipping")
                continue
            hits = d[header_len:]
            if len(hits) != 512:
                logging.warning(f"Frame at: {int(now)} has non-complete spokes, skipping")
                continue

            # TODO: do not send heading due to lack of GPS.
            # TODO: check and implement doppler speed and doppler state!
            spokes.append({"time": round(now, 5), "range_meters": range_meters, "spoke_index": scan_number,
                           "angle": angle, "rotation": rotation, "spoke": hits})

        if len(spokes) != 32:
            logging.warning(f"spokes at {int(now)} not complete, only got {len(spokes)}")

        return spokes  # TODO: publish

    def start(self):
        self.nControl.start()
        # time.sleep(2)
        self.nControl.set_halo_light(3)
        # time.sleep(2)
        # self.nControl.set_halo_light(0)
        # time.sleep(2)
        # self.nControl.set_halo_light(3)
        # time.sleep(2)

    def receive_spokes(self):
        logging.info("Start log spokes")

        signal.signal(signal.SIGINT, self.stop_handler)
        while self.do_receive_spokes:
            time.sleep(0.2) # TODO: evaluate sleep time to get all!
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
            pkts = sniff(iface=self.interface, filter=f"udp and dst port {self.nControl.addresses.addrReportB.port}", count=1, timeout=1) # might be to slow
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

