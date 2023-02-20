

DEGREES_PER_ROTATION = 360


def form_byte(pkt, start, end=-1, little=True, signed=False):
    if end == -1:
        end = start
    out = 0
    shift = 0 if little else 8*(end-start)
    try:
        for i in range(start, end + 1):
            out += int(pkt[i]) << shift
            if little:
                shift += 8
            else:
                shift -= 8
        return out
    except:
        print("Error:", len(pkt), pkt)
        raise ValueError(f"Index")


"""
// NEW GENERIC
#define SCALE_DEGREES_TO_SPOKES(angle)                                         \
    ((angle) * (m_ri->m_spokes) / DEGREES_PER_ROTATION)
#define SCALE_SPOKES_TO_DEGREES(raw)                                           \
    ((raw) * (double)DEGREES_PER_ROTATION / m_ri->m_spokes)
#define MOD_SPOKES(raw) (((raw) + 2 * m_ri->m_spokes) % m_ri->m_spokes)
#define MOD_DEGREES(angle)                                                     \
    (((angle) + 2 * DEGREES_PER_ROTATION) % DEGREES_PER_ROTATION)
#define MOD_DEGREES_FLOAT(angle)                                               \
    (fmod((double)(angle) + 2 * DEGREES_PER_ROTATION, DEGREES_PER_ROTATION))
#define MOD_DEGREES_180(angle) (((int)(angle) + 900) % 360 - 180)
"""

#def SCALE_DEGREES_TO_SPOKES(angle):


def good_hex(data):
    rows = []
    for i in range(0, len(data), 16):
        row = data[i:i+16].hex()
        o = []
        o.append(f"{i:04x}  ")
        for j in range(0, len(row), 2):
            o.append(row[j:j+2])
        rows.append(" ".join(o))
    return "\n".join(rows)


if __name__ == "__main__":
    d = b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    print(good_hex(d))
