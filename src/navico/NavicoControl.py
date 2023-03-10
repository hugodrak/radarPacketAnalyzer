
"""
Located radar IP 192.168.1.120 port 1, interface 192.168.1.187 [128773463/236.6.7.8:6678/236.6.7.9:6679/236.6.7.10:6680]


"""
import socket
import time
import struct

# sock = socket.socket(socket.AF_INET,  # Internet
# 		                     socket.SOCK_DGRAM)  # UDP


def send(ip, port, msg):
	for message in msg:
		print(message)
		sock.sendto(message, (ip, port))


# UDP_IP = "236.6.7.5"
# #UDP_IP = "192.168.1.120"
# #UDP_IP = "169.254.100.255"
#
# UDP_PORT = 6878
# MESSAGE = b"Hello, World!"
#
# pkt = [bytes([0xA0, 0xC1]), bytes([0x03, 0xC2]), bytes([0x04, 0xC2]), bytes([0x05, 0xC2])]
# #messages = [bytes([0x01, 0xb1])]
# #message.extend(len(message))
# # works
# send("236.6.7.4", 6878, [bytes([0x01, 0xb1])])
# time.sleep(10)
# send("236.6.7.13", 6680, pkt)
# send("236.6.7.14", 6002, pkt)


#---------------------

RadarReport_01B2_format = "<H16s6s12s6s4s6s10s6s4s6s10s6s4s6s10s6s4s6s10s6s4s6s10s6s4s6s10s6s4s6s"

pkt = [bytes([0xA0, 0xC1]), bytes([0x03, 0xC2]), bytes([0x04, 0xC2]), bytes([0x05, 0xC2])]


def capture_01B1():
	UDP_IP = "0.0.0.0"#"236.6.7.5"
	UDP_PORT = 6878

	# Create a UDP socket
	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

	# Bind the socket to the IP address and port
	sock.bind((UDP_IP, UDP_PORT))

	while True:
		data, addr = sock.recvfrom(60) # buffer size is 1024 bytes
		print("received message: %s" % data)
		if len(data) > 200:
			if data[0] == 0x01 and data[1] == 0xB2:
				print("received message: %s" % data)
				vars = struct.unpack(RadarReport_01B2_format, data)


def special():
	UDP_IP = "236.7.6.5"
	UDP_PORT = 6878
	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP
	sock.bind((UDP_IP, UDP_PORT))


	while True:
		sock.sendto(bytes([0x88, 0x99]), (UDP_IP, 6878))
		data, addr = sock.recvfrom(60)
		print(data, addr)
		time.sleep(1)





def main():
	while True:
		mode = input("Input mode: [0:monitor, 1: wakeup, 2:packets, 3:tx on, 4:tx off]")

		match mode:
			case "0":
				capture_01B1()
			case "1":
				#send("236.6.7.5", 6878, [bytes([0x01, 0xb1])])
				send("127.0.0.1", 6878, [bytes([0x01, 0xb1])])
				#capture_01B1()
			case "2":
				send("236.6.7.13", 6680, pkt)
				send("236.6.7.14", 6002, pkt)
			case "3":
				send("236.6.7.10", 6680, [bytes([0x00, 0xc1, 0x01])])
				send("236.6.7.10", 6680, [bytes([0x01, 0xc1, 0x01])])
			case "4":
				send("236.6.7.10", 6680, [bytes([0x00, 0xc1, 0x01])])
				send("236.6.7.10", 6680, [bytes([0x01, 0xc1, 0x01])])
			case "s":
				special()
			case "q":
				break



if __name__ == "__main__":
	main()
