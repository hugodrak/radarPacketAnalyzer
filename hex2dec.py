import argparse
parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('--little', '-l',  action="store_true", default=False, help='Little endian, default big')
#parser.add_argument('--signed', '-s', action="store_true", default=False, help="signed or not, default unsigned")
args = parser.parse_args()
while True:
	h = input(">>> ")
	if args.little:
		hs = "".join(h.split(" ")[::-1])
	else:
		hs = "".join(h.split(" "))
	print(int(hs, 16))
