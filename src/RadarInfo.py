from src.constants import RadarControlState


class RadarInfo:
	def __init__(self, radar):
		self._radar = radar
		self._arpa = 0
		self._range = 0
		self._timed_run = 0
		self._timed_idle = 0
		self._course_index = 0
		self._old_range = 0
		self._dir_lat = 0
		self._dir_lon = 0
		self._pixels_per_meter = 0.
		self._previous_auto_range_meters = 0
		self._stayalive_timeout = 0
		self._radar_timeout = 0
		self._data_timeout = 0
		self._history = 0
		self._polar_lookup = 0
		self._spokes = 0
		self._spoke_len_max = 0
		self._trails = 0
		self._idle_standby = 0
		self._idle_transmit = 0
		self._doppler_count = 0
		self._showManualValueInAuto = False
		self._timed_idle_hardware = False
		self._status_text_hide = False
		self._radar_location_info = None
		self._radar_interface_address = None
		self._radar_address = None
		self._last_rotation_time = 0
		self._last_angle = 0

		self._control = 0
		self._receive = 0
		self._draw_time_ms = 1000
		self._radar_panel = 0
		self._radar_canvas = 0
		self._control_dialog = 0
		self._state = False
		self._refresh_millis = 50

		self._drag_x = 0.
		self._drag_y = 0.
		self._off_center_x = 0.
		self._off_center_y = 0.
		self._panel_zoom = 0.
		self._view_center = 1
		self._radar_type = 0

		self._magnetron_time = 0
		self._rotation_period = 0
		self._magnetron_current = 0
		self._rotation_period = 0

		self._range_adjustment = 0
		self._quantum2type = False
		self._min_contour_length = 6
		self._threshold = 0
		self._main_bang_size = 0
		self._antenna_forward = 0
		self._antenna_starboard = 0
		self._range_adjustment = 0
		self._timed_run = 0