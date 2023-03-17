import socket
import threading
import time
from scapy.all import sniff, UDP, Ether, IP, send, Raw



def send_udp_packet(host, port):
    time.sleep(1)
    message = b'\x01\xb1'
    send(IP(dst="236.6.7.5") / UDP(dport=6878) / Raw(load=b'\x01\xb1'))
    print(f"Sent UDP packet: {message}")

def receive_udp_packet(port):
    f = "udp and dst host 236.6.7.5 and dst port 6878"

    data = sniff(iface="en7", filter=f, timeout=5, count=10)
    print(f"Received UDP packet from : {data}")

def main():
    host = "236.6.7.5"
    port = 6878

    # Start the receive thread
    receive_thread = threading.Thread(target=receive_udp_packet, args=(port,))
    receive_thread.daemon = True
    receive_thread.start()

    # Start the send thread
    send_thread = threading.Thread(target=send_udp_packet, args=(host, port))
    send_thread.start()

    # Wait for the send thread to complete

    send_thread.join()
    receive_thread.join()

if __name__ == "__main__":
    main()
