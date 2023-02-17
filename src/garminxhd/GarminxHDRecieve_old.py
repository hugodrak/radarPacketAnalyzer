from src.RadarRecieve import RadarRecieve
import struct
RADAR_LINE_FORMAT = "xxxxxxxxIIxxHHxxIIxxHxxIxxBBBB"
print(struct.calcsize(RADAR_LINE_FORMAT))
"""
  uint32_t packet_type;
  uint32_t len1;
  uint16_t fill_1;
  uint16_t scan_length;
  uint16_t angle;
  uint16_t fill_2;
  uint32_t range_meters;
  uint32_t display_meters;
  uint16_t fill_3;
  uint16_t scan_length_bytes_s;  // Number of video bytes in the packet, Short
  uint16_t fills_4;
  uint32_t scan_length_bytes_i;  // Number of video bytes in the packet, Integer
  uint16_t fills_5;
  uint8_t line_data[GARMIN_XHD_MAX_SPOKE_LEN];
  """
#print(struct.unpack("IIHHHIH", b"\x78\x0e\x00\x00\x47\x10\x00\x00\x00\x00\xb7\x02\x08\x01\xb7\x02\x00\x00\x00\x00\x00\x00"))
ex = b'\x98\x09\x00\x00\xd3\x02\x00\x00\x01\x00\xd3\x02\xf0\x03\x00\x00\x78\x0e\x00\x00\x47\x10\x00\x00\x00\x00\x00\x00\xb7\x02\x08\x01\xb7\x02\x00\x00\x00\x00\x00\x00'
ex2 = b'\xc3\xb6\xc3\xb6\x02\xe3\x86`\x98\t\x00\x00\xd3\x02\x00\x00\x01\x00\xd3\x02\xd8\x16\x00\x00x\x0e\x00\x00G\x10\x00\x00\x00\x00\xb7\x02\x08\x01\xb7\x02\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08'
print("ex", len(ex2))
print(struct.unpack(RADAR_LINE_FORMAT, ex2))





class GarminxHDRecieve(RadarRecieve):
	def process_frame(self, data, len):
		pass