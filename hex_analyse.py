

with open("output/raw_out", "r") as f:
	prev = []
	for line in f:
		hex = [int(x, 16) for x in line.split(" ")]
		# important = [hex[0], hex[1]] + hex[4:8] + hex[10:14]
		# if important != prev:
		# 	print(" ".join([f"{x:02x}" for x in important]))
		# prev = important
		range = (hex[15] & 0xff) << 8 + (hex[14] & 0xff)
		print(range)
