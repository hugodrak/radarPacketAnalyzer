COURSE_SAMPLES = 16
BLOB_HISTORY_MAX = 0
import numpy as np

class RadarInfo:
    def __init__(self):
        self.m_main_bang_size = 0
        self.m_threshold = 0
        self.m_radar_timeout = 0
        self.m_data_timeout = 0
        self.m_state = "RADAR_OFF"
        self.m_spokes = 0
        self.m_missing_spokes = 0
        self.m_range = 0
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

        self.m_history = [[[0]*512,0, 0]]*4096 # (line, time, pos)

    def process_radar_spokes(self, angle, bearing, line_data, length, range_meters, time_rec):
        self.sample_course(angle)
        self.calculate_rotation_speed(angle, time_rec)
        if range_meters == 0:
            raise ValueError("Error process_radar_spokes range is zero")  # logging

        for i in range(self.m_main_bang_size):
            line_data[i] = 0

        thresh = self.m_threshold
        if thresh > 0:
            thresh *= (255 - BLOB_HISTORY_MAX) / 100 + BLOB_HISTORY_MAX
            for i in range(length):
                if line_data[i] < thresh:
                    line_data[i] = 0

        ppm = (length / range_meters) * (1. - self.m_range_adjustment * 0.001)

        if self.m_pixels_per_meter != ppm:
            print(f"Detected spoke change rate from {self.m_pixels_per_meter} to {ppm} pixels/m, {range_meters}")
            self.m_pixels_per_meter = ppm
            self.m_history = []

        #orientation = 0 # implement self.get_orientation() 0=North
        ## -------- Start processing ---------
        #weakest_normal_blob = self.m_threshold_red
        #hist_data = self.m_history[bearing].line
        self.m_history[bearing].time = time_rec
        self.m_history[bearing].line = line_data

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