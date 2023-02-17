from scapy.utils import RawPcapReader
from scapy.layers.l2 import Ether
from scapy.layers.inet import IP, UDP


SOURCE_IP = '192.18.1.125'

log_path = "logs/quantum_1.pcap"
for (pkt_data, pkt_metadata,) in RawPcapReader(log_path):
            ether_pkt = Ether(pkt_data)
            good_packet = False
            if 'type' in ether_pkt.fields:
                if ether_pkt.type == 0x0800:
                    ip_pkt = ether_pkt[IP]
                    if ip_pkt.proto == 17:
                        if ip_pkt.src == SOURCE_IP:
                            udp_pkt = ether_pkt[UDP]
                            if udp_pkt.len >= 100:
                                good_packet = True