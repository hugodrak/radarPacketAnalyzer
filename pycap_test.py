import argparse
import os
import sys
from scapy.utils import RawPcapReader
from scapy.layers.l2 import Ether
from scapy.layers.inet import IP, UDP

source = '172.16.2.0'


def process_pcap(file_name):
	print('Opening {}...'.format(file_name))

	count = 0
	interesting_packet_count = 0

	for (pkt_data, pkt_metadata,) in RawPcapReader(file_name):
		count += 1

		ether_pkt = Ether(pkt_data)
		if 'type' not in ether_pkt.fields:
			# LLC frames will have 'len' instead of 'type'.
			# We disregard those
			continue

		if ether_pkt.type != 0x0800:
			# disregard non-IPv4 packets
			continue

		ip_pkt = ether_pkt[IP]
		if ip_pkt.proto != 17: # 6 = TCP, 17 = UDP
			# Ignore non-UDP packet
			continue

		if ip_pkt.src != source:
			continue

		udp_pkt = ether_pkt[UDP]
		if udp_pkt.len < 10:
			continue


		interesting_packet_count += 1

	print('{} contains {} packets ({} interesting)'.format(file_name, count, interesting_packet_count))

process_pcap("logs/garmin_small/out_00000_20171020010451.pcap")