
"""
Located radar IP 192.168.1.120 port 1, interface 192.168.1.187 [128773463/236.6.7.8:6678/236.6.7.9:6679/236.6.7.10:6680]


"""
import socket


def send(ip, port, msg):
	for message in msg:
		print(message)
		sock = socket.socket(socket.AF_INET,  # Internet
		                     socket.SOCK_DGRAM)  # UDP
		sock.sendto(message, (ip, port))


UDP_IP = "236.6.7.5"
#UDP_IP = "192.168.1.120"
#UDP_IP = "169.254.100.255"

UDP_PORT = 6878
MESSAGE = b"Hello, World!"

pkt = [bytes([0xA0, 0xC1]), bytes([0x03, 0xC2]), bytes([0x04, 0xC2]), bytes([0x05, 0xC2])]
#messages = [bytes([0x01, 0xb1])]
#message.extend(len(message))
# works
send("236.6.7.5", 6878, [bytes([0x01, 0xb1])])
send("236.6.7.13", 6680, pkt)
send("236.6.7.14", 6002, pkt)

while True:
	pass



