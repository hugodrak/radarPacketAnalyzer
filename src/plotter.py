import logging

import matplotlib.pyplot as plt
import numpy as np
import logging
from matplotlib.animation import FFMpegWriter
import os
from datetime import datetime
import time
import cv2


cv_font = cv2.FONT_HERSHEY_SIMPLEX


def figure_to_array(fig):
    fig.canvas.draw()
    return np.array(fig.canvas.renderer._renderer)


class Plotter:
	def __init__(self, title, out_path):
		if not os.path.exists(out_path):
			raise IOError(f"Out path {out_path} does not exist!")
		self.title = title
		self.frames = 0
		self.t_start = 0
		self.t_end = 0

		self.fig = plt.figure()
		self.ax = self.fig.add_subplot(111)
		self.out_file_path = os.path.join(out_path,
		                                  f"{self.title}_{datetime.strftime(datetime.now(), '%y%m%d_%H%M')}.mp4")

		#metadata = dict(title='RadarAnimation', artist='EENX16_23_02', comment='COOl radars right?!')
		#self.writer = FFMpegWriter(fps=6, metadata=metadata)
		#self.writer.setup(self.fig, self.out_file_path, 200)
		#cv2 stuff
		self.size = 960, 960
		fps = 5.8
		#fourcc = cv2.VideoWriter_fourcc('M', 'J', 'P', 'G')
		#fourcc = cv2.VideoWriter_fourcc(*'mp4V')
		self.cvout = cv2.VideoWriter(self.out_file_path, 0x7634706d, fps, self.size, True)

	def update2(self, mat, ts):
		if self.t_start == 0:
			self.t_start = ts
		self.ax.clear()  # important
		self.ax.imshow(mat, cmap='jet', interpolation='nearest')

		self.frames += 1
		self.ax.set_title(self.title + f"t:{round(ts)}, f:{self.frames}")
		self.ax.set_ylabel('      AFT <-- (meters) --> STERN    ')
		self.ax.set_xlabel('     PORT <-- (meters) --> STARBOARD')
		#plt.show()
		self.t_end = ts
		#t1 = time.time()
		self.writer.grab_frame()
		#print(f"plott: {round((time.time() - t1) * 1000)}ms")

	def update3(self, mat, ts):
		if self.t_start == 0:
			self.t_start = ts
		self.ax.clear()
		self.ax.imshow(mat, cmap='jet', interpolation='nearest')

		self.frames += 1
		self.ax.set_title(self.title + f"t:{round(ts)}, f:{self.frames}")
		self.ax.set_ylabel('      AFT <-- (meters) --> STERN    ')
		self.ax.set_xlabel('     PORT <-- (meters) --> STARBOARD')
		# fig = plt.figure()
		# ax = fig.add_subplot(111)
		# xpoints = np.array([1, 8])
		# ypoints = np.array([3, 10])
		# ax.plot(xpoints, ypoints, "-r")

		#plt.show()
		self.t_end = ts


		f_arr = figure_to_array(self.fig)
		f_arr = cv2.resize(f_arr, (1000, 1000))

		bgr = cv2.cvtColor(f_arr, cv2.COLOR_RGBA2BGR)
		# cv2.imshow('f_arr', bgr)
		# cv2.waitKey(0)
		self.cvout.write(bgr)

		print(f"plott: {round((time.time() - t1) * 1000)}ms")

	def update(self, mat, ts):
		#t1 = time.time()
		heatmap = cv2.resize(mat, self.size)

		img = None
		img =cv2.normalize(heatmap, img, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8U)
		img = cv2.applyColorMap(img, cv2.COLORMAP_JET)
		text = self.title + f" t:{round(ts)}, f:{self.frames}"
		img = cv2.putText(img, text, (50, 50), cv_font, 1, (0, 255, 0), 2, cv2.LINE_AA)
		self.frames += 1
		# cv2.imshow("Heatmap", heatmapshow)
		# cv2.waitKey(0)
		self.cvout.write(img)
		#print(f"plott: {round((time.time() - t1) * 1000)}ms")

	def finish(self):
		self.cvout.release()
		logging.info(f"Written animation: {self.out_file_path}, with: {self.frames} frames")
		#self.writer.finish()


if __name__ == "__main__":
	pl = Plotter("hej")
	mat = np.zeros((25, 25), dtype=np.int8)
	mat[10][10] = 100
	pl.update(mat)
	pl.finish()