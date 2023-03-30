COURSE_SAMPLES = 16
BLOB_HISTORY_MAX = 0
import numpy as np
import math
import logging
import time


class RadarHistory:
    #line = np.zeros(512, dtype=np.uint8)
    time = 0.0
    pos = (0.0, 0.0)

    def __repr__(self):
        return f"({int(self.time)}, Lat:{self.pos[0]}, Lon:{self.pos[1]})"


class RadarInfo:
    def __init__(self, spokes):
        # control parameters
        self.m_radar_status = 0
        self.m_gain = 0
        self.m_rain = 0
        self.m_sea = 0
        self.m_mode = 0
        self.m_target_boost = 0
        self.m_interference_rejection = 0
        self.m_target_expansion = 0
        self.m_range = 0
        self.m_bearing_alignment = 0
        self.m_antenna_height = 0
        self.m_halo_light = 0

        self.m_main_bang_size = 0
        self.m_threshold = 0
        self.m_radar_timeout = 0
        self.m_data_timeout = 0
        self.m_state = "RADAR_OFF"
        self.m_spokes = spokes
        self.m_first_found = False
        self.m_missing_spokes = 0
        self.m_range_adjustment = 0
        self.m_pixels_per_meter = 0.
        self.m_arpa = 0
        self.m_course_index = 0
        self.m_heading = 0.  # this is something we need to get from the gps
        self.m_course_log = np.zeros(COURSE_SAMPLES)
        self.m_course = 0.
        self.m_last_angle = 0.
        self.m_last_rotation_time = 0.
        self.m_rotation_period = 0
        self.m_threshold_red = 200
        self.m_doppler_count = 0
        self.m_doppler_spokes = np.zeros((2048, 512), dtype=np.uint8)  # 1: approaching 2: receding
        self.m_doppler_state = 0
        self.m_doppler_speed = 0
        self.steps = 512
        self.last_timestamp = 0
        self.m_history_bangs = np.zeros((2048, 512), dtype=np.uint8)
        self.m_history = []  #[[[0]*512, 0, 0]]*self.m_spokes  # (line, time, pos)
        for i in range(self.m_spokes):
            self.m_history.append(RadarHistory())

    def process_radar_spokes(self, angle, bearing, line_data, length, range_meters, time_rec):
        self.last_timestamp = time_rec
        #self.sample_course(angle)
        self.calculate_rotation_speed(angle, time_rec)
        if range_meters == 0:
            raise ValueError("Error process_radar_spokes range is zero")  # logging

        # for i in range(self.m_main_bang_size):
        #     line_data[i] = 0

        # thresh = self.m_threshold
        # if thresh > 0:
        #     thresh *= (255 - BLOB_HISTORY_MAX) / 100 + BLOB_HISTORY_MAX
        #     for i in range(length):
        #         if line_data[i] < thresh:
        #             line_data[i] = 0

        ppm = (length / range_meters) * (1. - self.m_range_adjustment * 0.001)

        if self.m_pixels_per_meter != ppm:
            print(f"Detected spoke change rate from {self.m_pixels_per_meter} to {ppm} pixels/m, Range: {range_meters} m")
            self.m_pixels_per_meter = ppm
            #self.m_history = []  # TODO: Why?

        #orientation = 0 # implement self.get_orientation() 0=North
        ## -------- Start processing ---------
        #weakest_normal_blob = self.m_threshold_red
        #hist_data = self.m_history[bearing].line
        # TODO: position
        if 0 < bearing < len(self.m_history):
            self.m_history[bearing].time = time_rec
            self.m_history_bangs[bearing] = np.frombuffer(line_data, dtype=np.uint8)
        else:
            h=0




        # for radius in range(length):
        #     if line_data[radius] >= weakest_normal_blob:
        #         # and add 1 of above threshold and set the left 2 bits, used for ARPA
        #         hist_data[radius] = 192  # this is C0, 1100 0000
        #     if line_data[radius] == 255:
        #         # approaching doppler targets
        #         # and add 1 of above threshold and set the left 2 bits, used for ARPA
        #         hist_data[radius] = 0xE0  # this is  1110 0000, bit 3 indicates this is an approaching target
        #         self.m_doppler_count += 1

        ## TODO: implement guard zones

    def sample_course(self, angle):
        # Calculates the moving average of m_hdt and returns this in m_course
        # This is a bit more complicated then expected, average of 359 and 1 is 180 and that is not what we want
        if (angle and 127) == 0:
            if self.m_course_log[self.m_course_index] > 720.:
                for i in range(0, COURSE_SAMPLES):
                    self.m_course_log[i] -= 720.
            if self.m_course_log[self.m_course_index] < -720.:
                for i in range(0, COURSE_SAMPLES):
                    self.m_course_log[i] += 720.
            hdt = self.m_heading

            while self.m_course_log[self.m_course_index] - hdt > 180.:
                hdt += 360.

            while self.m_course_log[self.m_course_index] - hdt < -180.:
                hdt -= 360.

            self.m_course_index += 1
            if self.m_course_index >= COURSE_SAMPLES:
                self.m_course_index = 0

            self.m_course_log[self.m_course_index] = hdt
            summ = 0
            for i in range(0, COURSE_SAMPLES):
                summ += self.m_course_log[i]

            self.m_course = math.fmod(summ/COURSE_SAMPLES + 720., 360)

    def calculate_rotation_speed(self, angle, time_rec):
        if angle < self.m_last_angle:
            if self.m_last_rotation_time != 0 and time_rec > self.m_last_rotation_time + 100:
                delta = time_rec - self.m_last_rotation_time
                self.m_rotation_period = int(delta)
            self.m_last_rotation_time = time_rec
        self.m_last_angle = angle

    def to_plotter2(self):
        print(f"Processing for time {self.last_timestamp}")
        mat = np.zeros((self.steps*2 + 1, self.steps*2 + 1), dtype=np.uint16)
        for si, hist in enumerate(self.m_history):
            spoke = hist.line
            a = (si/self.steps)*2*np.pi
            for h, bang in enumerate(spoke):
                m = (h + 1) * np.sin(a)
                n = (h + 1) * np.cos(a)

                x = round(self.steps + m)
                y = round(self.steps - n)
                if x < 0 or y < 0:
                    raise ValueError("Reverse indexes not allowed!")

                mat[y][x] = bang#(mat[y][x]+bang)//2

        return mat

    def to_plotter(self):
        t1 = time.time()
        #matrix = np.zeros((1025, 1025), dtype=np.uint8)
        # angles = np.linspace(0, 2 * np.pi, 2048, endpoint=False)

        # for i in range(2048):
        #     angle = i * 2 * np.pi / 2048
        #
        #     indexes = np.linspace(0, 512, 512)
        #     x = np.sin(angle) * indexes
        #     y = np.cos(angle) * indexes
        #
        #     x2 = np.round(512+x).astype(int)
        #     y2 = np.round(512-y).astype(int)
        #     matrix[y2, x2] = self.m_history_bangs[i, :]
        #
        # return matrix
        matrix = np.zeros((1025, 1025), dtype=np.uint8)
        angles = np.arange(2048) * 2 * np.pi / 2048

        indexes = np.linspace(0, 512, 512)
        x = np.sin(angles[:, np.newaxis]) * indexes
        y = np.cos(angles[:, np.newaxis]) * indexes

        x2 = np.round(512 + x).astype(int)
        y2 = np.round(512 - y).astype(int)

        matrix[y2.flatten(), x2.flatten()] = self.m_history_bangs.ravel()
        matrix = matrix.astype(np.float32)
        matrix /= 255
        #print(f"MAT for t={self.last_timestamp}, td={round((time.time()-t1)*1000, 4)}")
        return matrix

