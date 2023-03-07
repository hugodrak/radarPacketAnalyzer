import logging

import matplotlib.pyplot as plt
import numpy as np
import logging
from matplotlib.animation import FFMpegWriter
import os
from datetime import datetime

class Plotter:
	def __init__(self, title, out_path):
		if not os.path.exists(out_path):
			raise IOError(f"Out path {out_path} does not exist!")
		self.title = title
		metadata = dict(title='RadarAnimation', artist='EENX16_23_02',
		                comment='COOl radars right?!')
		self.writer = FFMpegWriter(fps=20, metadata=metadata)
		self.fig = plt.figure()
		self.ax = self.fig.add_subplot(111)
		self.out_file_path = os.path.join(out_path, f"{self.title}_{datetime.strftime(datetime.now(), '%y%m%d_%H%M')}.mp4")
		self.writer.setup(self.fig, self.out_file_path, 100)

	def update(self, mat):
		self.ax.imshow(mat, cmap='viridis', interpolation='nearest')
		self.ax.set_title(self.title)

		self.ax.set_ylabel('      AFT <-- (meters) --> STERN    ')
		self.ax.set_xlabel('     PORT <-- (meters) --> STARBOARD')
		#plt.show()
		self.writer.grab_frame()

	def finish(self):
		logging.info(f"Written animation: {self.out_file_path}")
		self.writer.finish()


if __name__ == "__main__":
	pl = Plotter("hej")
	mat = np.zeros((25, 25), dtype=np.int8)
	mat[10][10] = 100
	pl.update(mat)
	pl.finish()