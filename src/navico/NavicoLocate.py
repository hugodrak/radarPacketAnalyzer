import threading
import queue
import time
from src.tools import transmit_cmd, packet_addr, NetworkAddr
from scapy.all import sniff, UDP, Ether, IP, get_if_list
import struct

WAKE_ADDR = NetworkAddr("236.6.7.5", 6878)


def wake_radar():
	time.sleep(1)
	transmit_cmd(WAKE_ADDR, b'\x01\xb1')


def receive_udp_packet(iface, received_queue):
	f = "udp and dst host 236.6.7.5 and dst port 6878"

	found = False
	while not found:
		res = sniff(iface=iface, filter=f, timeout=2, count=3)
		# print(res)
		if len(res) > 0:
			for pkt in res:
				# print(len(pkt))
				if pkt[Ether][IP].haslayer(UDP):
					if pkt[Ether][IP][UDP].dport == 6878 and pkt[Ether][IP].dst == "236.6.7.5":
						udp = pkt[Ether][IP][UDP]
						if "load" in dir(udp.payload):
							payload = udp.payload.load
							if payload[:2] == b'\x01\xb2':
								# print(pkt)
								# print(f"Received UDP packet from : {payload}")
								received_queue.put(payload)
								return True


class NavicoInfo:
	id = 0
	serialno = ""
	addr0 = None
	addrDataA = None
	addrSendA = None
	addrReportA = None
	addrDataB = None
	addrSendB = None
	addrReportB = None
	acquired = False

	def load(self, d):
		self.id = d["id"]
		self.serialno = d["serialno"]
		self.addr0 = d["addr0"]
		self.addrDataA = d["addrDataA"]
		self.addrSendA = d["addrSendA"]
		self.addrReportA = d["addrReportA"]
		self.addrDataB = d["addrDataB"]
		self.addrSendB = d["addrSendB"]
		self.addrReportB = d["addrReportB"]
		self.acquired = True


class NavicoLocate:
	interface = "en7"
	RadarReport_01B2_format = "<H16s6s12s6s4s6s10s6s4s6s10s6s4s6s4s6s10s6s4s6s4s6s10s6s4s6s4s6s10s6s4s6s4s6s"

	def __init__(self):
		self.last_packet = None
		self.addr_acquired = False
		self.nInfo = NavicoInfo()
		if not self.interface in get_if_list():
			raise ValueError(f"Interface {self.interface} not available!")

	def locate(self):
		# First thing to run so that 01b2 packet can be found.
		# Create a queue for communication between threads
		received_queue = queue.Queue()
		# Start the receive threadr
		receive_thread = threading.Thread(target=receive_udp_packet, args=(self.interface, received_queue,))
		receive_thread.daemon = True
		receive_thread.start()

		# Start the send thread
		send_thread = threading.Thread(target=wake_radar)
		send_thread.start()

		# Wait for the send thread to complete

		send_thread.join()
		receive_thread.join()
		data = received_queue.get()
		report = self.process_report(data)
		self.nInfo.load(report)
		self.addr_acquired = True




	def process_report(self, data):
		vars = struct.unpack(self.RadarReport_01B2_format, data)
		out = {"id": vars[0],
		       "serialno": "".join([chr(x) if x != 0 else "" for x in vars[1]]),
		       "addr0": packet_addr(vars[2]),
		       # "addr1": packet_addr(vars[4]),
		       # "addr2": packet_addr(vars[6]),
		       # "addr3": packet_addr(vars[8]),
		       # "addr4": packet_addr(vars[10]),
		       "addrDataA": packet_addr(vars[12]),
		       "addrSendA": packet_addr(vars[14]),
		       "addrReportA": packet_addr(vars[16]),
		       "addrDataB": packet_addr(vars[18]),
		       "addrSendB": packet_addr(vars[20]),
		       "addrReportB": packet_addr(vars[22]),
		       # "addr11": packet_addr(vars[24]),
		       # "addr12": packet_addr(vars[26]),
		       # "addr13": packet_addr(vars[28]),
		       # "addr14": packet_addr(vars[30]),
		       # "addr15": packet_addr(vars[32]),
		       # "addr16": packet_addr(vars[34]),
		       }
		return out
