import matplotlib.pyplot as plt
import numpy as np


class Plotter:
	def __init__(self, title):
		self.title = title

	def update(self, mat):
		plt.imshow(mat, cmap='plasma', interpolation='nearest')
		plt.title(self.title)

		plt.ylabel('AFT <--      (meters)   --> STERN')
		plt.xlabel('PORT <--       (meters) --> STARBOARD')
		plt.show()