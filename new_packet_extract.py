import argparse
import os
import sys
from scapy.utils import RawPcapReader
from scapy.layers.l2 import Ether
from scapy.layers.inet import IP, UDP

source = '192.168.8.137'


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
		if udp_pkt.len < 10000:
			continue


		interesting_packet_count += 1

	print('{} contains {} packets ({} interesting)'.format(file_name, count, interesting_packet_count))


if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='PCAP reader')
	parser.add_argument('--pcap', metavar='<pcap file name>',
						help='pcap file to parse', required=True)
	args = parser.parse_args()

	file_name = args.pcap
	if not os.path.isfile(file_name):
		print('"{}" does not exist'.format(file_name), file=sys.stderr)
		sys.exit(-1)

	process_pcap(file_name)
	sys.exit(0)