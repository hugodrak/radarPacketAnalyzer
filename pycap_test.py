import time

from scapy.all import sniff, UDP, Ether, IP
import struct
import threading
import queue
import socket
# udp_sock = socket.socket(socket.AF_INET,  # Internet
#                              socket.SOCK_DGRAM)  # UDP
from src.navico.NavicoControl import send



# print(packet_addr(b'\xc0\xa8\x01x\x011'))
# d = b'\x01\xb2128773463\x00\x00\x00\x00\x00\x00\x00\xc0\xa8\x01x\x011\x06\x00\xfd\xff \x01\x02\x00\x10\x00\x00\x00\xec\x06\x07\x0c\x17p\x11\x00\x00\x00\xec\x06\x07\x16\x1a&\x1f\x00 \x01\x02\x00\x10\x00\x00\x00\xec\x06\x07\x17\x1a\x1c\x11\x00\x00\x00\xec\x06\x07\x18\x1a\x1d\x10\x00 \x01\x03\x00\x10\x00\x00\x00\xec\x06\x07\x08\x1a\x16\x11\x00\x00\x00\xec\x06\x07\n\x1a\x18\x12\x00\x00\x00\xec\x06\x07\t\x1a\x17\x10\x00 \x02\x03\x00\x10\x00\x00\x00\xec\x06\x07\r\x17q\x11\x00\x00\x00\xec\x06\x07\x0e\x17r\x12\x00\x00\x00\xec\x06\x07\r\x17s\x12\x00 \x01\x03\x00\x10\x00\x00\x00\xec\x06\x07\x12\x1a \x11\x00\x00\x00\xec\x06\x07\x14\x1a"\x12\x00\x00\x00\xec\x06\x07\x13\x1a!\x12\x00 \x02\x03\x00\x10\x00\x00\x00\xec\x06\x07\r\x17t\x11\x00\x00\x00\xec\x06\x07\x0f\x17u\x12\x00\x00\x00\xec\x06\x07\r\x17v'


class PacketAddr:
    def __init__(self, addr, port):
        self.addr = addr
        self.port = port

    def __repr__(self):
        return f"{self.addr}:{self.port}"


class Radar:
    def __init__(self):
        self.id = 0
        self.serialno = ""
        self.addr0 = None
        self.addrDataA = None
        self.addrSendA = None
        self.addrReportA = None
        self.addrDataB = None
        self.addrSendB = None
        self.addrReportB = None
        self.acquired = False

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


def packet_addr(data):
   #return ".".join([str(x) for x in data[:-2]])+":"+str(data[-2] << 8 | data[-1])
   return PacketAddr(".".join([str(x) for x in data[:-2]]), (data[-2] << 8 | data[-1]))


# def send(ip, port, msg):
#
#     for message in msg:
#         print(message)
#         udp_sock.sendto(message, (ip, port))


def parse01B1(data):
   # print(len(data))
   # print(" ".join([f'{x:02X}' for x in data]))
   RadarReport_01B2_format = "<H16s6s12s6s4s6s10s6s4s6s10s6s4s6s4s6s10s6s4s6s4s6s10s6s4s6s4s6s10s6s4s6s4s6s"
   vars = struct.unpack(RadarReport_01B2_format, data)
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


   # print(vars)
   # print(out)
   return out


# def capture_01B1(pkt):
#     if pkt.haslayer(Ether):
#         if pkt[Ether].haslayer(IP):
#             if pkt[Ether][IP].haslayer(UDP):
#                 if pkt[Ether][IP][UDP].dport == 6878 and pkt[Ether][IP].dst == "236.6.7.5":
#                     udp = pkt[Ether][IP][UDP]
#                     print(pkt)
#                     return parse01B1(udp.payload.load)


def listen_01B1():
    f = "udp and dst host 236.6.7.5 and dst port 6878"
    #f = "udp"
    return sniff(iface="en7", filter=f, timeout=1, count=10)


def send_udp_packet():
    time.sleep(1)
    #message = b'\x01\xb1'
    send("236.6.7.5", 6878, [bytes([0x01, 0xb1])])
    #send(IP(dst="236.6.7.5") / UDP(dport=6878) / Raw(load=b'\x01\xb1'))
    #print(f"Sent UDP packet: {message}")


def receive_udp_packet(received_queue):
    f = "udp and dst host 236.6.7.5 and dst port 6878"

    #data = sniff(iface="en7", filter=f, timeout=5, count=10)
    found = False
    while not found:
        res = sniff(iface="en7", filter=f, timeout=2, count=3)
        #print(res)
        if len(res) > 0:
            for pkt in res:
                #print(len(pkt))
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


def startup_seq():
    r = Radar()
    # Create a queue for communication between threads
    received_queue = queue.Queue()
    # Start the receive threadr
    receive_thread = threading.Thread(target=receive_udp_packet, args=(received_queue,))
    receive_thread.daemon = True
    receive_thread.start()

    # Start the send thread
    send_thread = threading.Thread(target=send_udp_packet)
    send_thread.start()

    # Wait for the send thread to complete

    send_thread.join()
    receive_thread.join()

    data = received_queue.get()
    r.load(parse01B1(data))
    print(r.__dict__)


    print("done")


if __name__ == "__main__":
    startup_seq()