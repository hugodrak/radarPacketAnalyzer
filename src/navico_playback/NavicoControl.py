import time

from src.navico_playback.NavicoLocate import NavicoLocate, NavicoInfo
from src.tools import transmit_cmd
import threading
import logging

logging.getLogger().setLevel(logging.INFO)


class NavicoControl:
	COMMAND_TX_OFF_A  = b'\x00\xc1\x01'
	COMMAND_TX_OFF_B  = b'\x01\xc1\x00'
	COMMAND_TX_ON_A   = b'\x00\xc1\x01'
	COMMAND_TX_ON_B   = b'\x01\xc1\x01'
	COMMAND_STAY_ON_A = b'\xA0\xc1'
	COMMAND_STAY_ON_B = b'\x03\xc2'
	COMMAND_STAY_ON_C = b'\x04\xc2'
	COMMAND_STAY_ON_D = b'\x05\xc2'

	def __init__(self, iface):
		self.interface = iface
		self.nLocate = NavicoLocate(self.interface)
		self.addresses = NavicoInfo
		self.m_send_address = None
		self.stayalive_thread = threading.Thread
		self.stop_heartbeat = False

	def start(self, log):
		logging.info("Start locating")
		self.nLocate.locate(log)
		if self.nLocate.addr_acquired:
			logging.info("Addresses acquired")
			self.addresses = self.nLocate.nInfo
			#print(self.addresses.__dict__)
			self.m_send_address = self.addresses.addrSendB  # might be B
			logging.info(f"Located radar on {self.m_send_address}")
			# if self.m_send_address:
			# 	self.start_stayalive_thread()

	def stop(self):
		self.stop_stayalive_thread()

	def transmit_cmd(self, msg):
		transmit_cmd(self.m_send_address, msg)

	def stayalive(self):
		logging.info("Stayalive pounding!")
		while not self.stop_heartbeat:
			transmit_cmd(self.addresses.addrSendA, self.COMMAND_STAY_ON_A)
			transmit_cmd(self.addresses.addrSendA, self.COMMAND_STAY_ON_B)
			transmit_cmd(self.addresses.addrSendA, self.COMMAND_STAY_ON_C)
			transmit_cmd(self.addresses.addrSendA, self.COMMAND_STAY_ON_D)
			transmit_cmd(self.addresses.addrSendB, self.COMMAND_STAY_ON_A)
			transmit_cmd(self.addresses.addrSendB, self.COMMAND_STAY_ON_B)
			transmit_cmd(self.addresses.addrSendB, self.COMMAND_STAY_ON_C)
			transmit_cmd(self.addresses.addrSendB, self.COMMAND_STAY_ON_D)
			time.sleep(4)

	def start_stayalive_thread(self):
		self.stayalive_thread = threading.Thread(target=self.stayalive)
		self.stayalive_thread.start()

	def stop_stayalive_thread(self):
		self.stop_heartbeat = True
		self.stayalive_thread.join()

	def RadarTxOff(self):
		self.transmit_cmd(self.COMMAND_TX_OFF_A)
		self.transmit_cmd(self.COMMAND_TX_OFF_B)
		logging.info("RadarTxOff sent")

	def RadarTxOn(self):
		self.transmit_cmd(self.COMMAND_TX_ON_A)
		self.transmit_cmd(self.COMMAND_TX_ON_B)
		logging.info("RadarTxOn sent")

	def set_range(self, meters):
		if meters >= 50 and meters <= 72704:
			decimeters = meters * 10
			pck = bytes([0x03,
		                 0xc1,
		                 (decimeters >> 0) & 0xFF,
		                 (decimeters >> 8) & 0xFF,
		                 (decimeters >> 16) & 0xFF,
		                 (decimeters >> 24) & 0xFF])
			self.transmit_cmd(pck)

	def set_gain(self, value):
		v = (value + 1) * 255 / 100
		if v > 255:
			v = 255
		# TODO: implement auto on index 6
		cmd = bytes([0x06, 0xc1, 0, 0, 0, 0, 0, 0, 0, 0, v])
		self.transmit_cmd(cmd)
		logging.info(f"Gain set to {v}")

	# TODO: check radar type
	def set_sea(self, value):
		v = (value + 1) * 255 / 100
		if v > 255:
			v = 255
		# TODO: implement auto on index 6
		cmd = bytes([0x06, 0xc1, 0, 0, 0, 0, 0, 0, 0, 0, v])
		self.transmit_cmd(cmd)
		logging.info(f"Sea clutter set to {v}")

	def set_rain(self, value):
		v = (value + 1) * 255 / 100
		if v > 255:
			v = 255
		# rain clutter is allways manual
		cmd = bytes([0x06, 0xc1, 0x04, 0, 0, 0, 0, 0, 0, 0, v])
		self.transmit_cmd(cmd)
		logging.info(f"Rain clutter set to {v}")

	def set_side_lobe_suppression(self, value):
		v = (value + 1) * 255 / 100
		if v > 255:
			v = 255
		cmd = bytes([0x06, 0xc1, 0x05, 0, 0, 0, 0, 0, 0, 0, v])
		self.transmit_cmd(cmd)
		logging.info(f"Side lobe suppression set to {v}")

	# TODO: what would command 7 be?

	def set_interference_rejection(self, v):
		cmd = bytes([0x08, 0xc1, v])
		self.transmit_cmd(cmd)
		logging.info(f"interference_rejection set to {v}")

	def set_target_expansion(self, v):
		cmd = bytes([0x09, 0xc1, v])
		self.transmit_cmd(cmd)
		logging.info(f"Target expansion set to {v}")

	def set_target_boost(self, v):
		cmd = bytes([0x0a, 0xc1, v])
		self.transmit_cmd(cmd)
		logging.info(f"Target boost set to {v}")

	# then comes some stuff we do not need like section blanking...

	def set_scan_speed(self, v):
		cmd = bytes([0x0f, 0xc1, v])
		self.transmit_cmd(cmd)
		logging.info(f"Scan speed set to {v}")

	def set_mode(self, v):
		cmd = bytes([0x10, 0xc1, v])
		self.transmit_cmd(cmd)
		logging.info(f"Mode set to {v}")

	def set_noise_rejection(self, v):
		cmd = bytes([0x21, 0xc1, v])
		self.transmit_cmd(cmd)
		logging.info(f"Noice rejection set to {v}")

	def set_doppler(self, v):
		cmd = bytes([0x23, 0xc1, v])
		self.transmit_cmd(cmd)
		logging.info(f"Doppler set to {v}")

	def set_antenna_height(self, value): # input shall be meters, radar wants mm
		v = int(value * 1000)
		v1 = v // 256
		v2 = v & 255
		cmd = bytes([0x30, 0xc1, 0x01, 0, 0, 0, v2, v1, 0, 0])
		self.transmit_cmd(cmd)
		logging.info(f"Antenna height set to {v} mm")

	def set_halo_light(self, v):  # 0, 1, 2, 3
		cmd = bytes([0x31, 0xc1, v])
		self.transmit_cmd(cmd)
		logging.info(f"Halo light set to {v}")


if __name__ == "__main__":
	nc = NavicoControl()
	nc.start()
	time.sleep(2)
	nc.set_halo_light(3)
	nc.set_antenna_height(2.05) #m
	#nc.RadarTxOff()
