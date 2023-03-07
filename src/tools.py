import matplotlib.pyplot as plt
import numpy as np

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


def debug_mat(mat):
    out = []
    for row in mat:
        out_row = []
        for c in row:
            out_row.append(" " if c == 0 else "1")
        out.append("".join(out_row))
    print("\n".join(out))
    print(f"Rows: {len(mat)}, Cols: {len(mat[0])}, Sum: {np.sum(mat)}")


def to_plotter(spokes):
    steps = len(spokes[0])
    mat = np.zeros((steps*2 + 1, steps*2 + 1), dtype=np.uint16)
    for si, spoke in enumerate(spokes):
        a = (si/len(spokes))*2*np.pi
        for h, bang in enumerate(spoke):
            m = (h+1)*np.sin(a)
            n = (h+1)*np.cos(a)

            x = round(steps+m)
            y = round(steps-n)
            if x < 0 or y < 0:
                raise ValueError("Reverse indexes not allowed!")

            mat[y][x] = (mat[y][x]+bang)//2
    return mat


def to_plotter2(spokes):
    num_steps = spokes.shape[1]
    angle_step = 2 * np.pi / spokes.shape[0]
    x, y = np.meshgrid(range(num_steps * 2 + 1), range(num_steps * 2 + 1))
    x = x.astype(np.float32) - num_steps
    y = y.astype(np.float32) - num_steps
    angles = np.arange(spokes.shape[0]) * angle_step
    radii = np.arange(num_steps)[:, np.newaxis] + 1

    # Compute polar coordinates (radius, angle) for each point in the grid
    r = np.sqrt(x ** 2 + y ** 2)
    a = np.arctan2(-y, x)  # note the negative y-coordinate to match the polar coordinate system

    # Compute the indices of the spokes and their weights
    si = (a / angle_step).astype(np.int32)
    sh = (r * np.cos(a - angles[si]) / radii).astype(np.int32)
    sw = (spokes[si, sh] / radii).astype(np.uint16)

    # Set the values in the output matrix using advanced indexing
    mat = np.zeros((num_steps * 2 + 1, num_steps * 2 + 1), dtype=np.uint16)
    mat[y >= 0, x >= 0] = sw[y >= 0, x >= 0]
    return mat


if __name__ == "__main__":
    spokes = np.zeros((2048, 512), dtype=np.uint8)
    for i in range(0,2048,682):
        spokes[i] = np.asarray([254]*512, dtype=np.uint8)
    for i in range(0, 2048):
        spokes[i][511] = 254
        spokes[i][200] = 254
    matt = to_plotter2(spokes)
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.set_title("hej")
    ax.imshow(matt, cmap='plasma')
    plt.show()