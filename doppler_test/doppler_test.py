import struct


def get_vars(format, data):
    unpacked = struct.unpack(format, data)
    return [x[0] if type(x) == bytes else x for x in unpacked]




a = bytearray.fromhex("08c401000101000000c0cf0002011900010000c800")
RadarReport_08C4_21 = "<ssssssssssHsssssssH"


v = get_vars(RadarReport_08C4_21, a)
print(v[17:])