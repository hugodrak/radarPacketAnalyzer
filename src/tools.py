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