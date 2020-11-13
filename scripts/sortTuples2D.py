###########################
# Sort Tuples by XY       #
###########################

# This script is used to sort a list of tuples across 2 dimensions
# Created by Justin Miller on 11.12.2020

# USAGE:
# python3 sortTuplesByXY.py

# Import packages
import numpy as np

# Generate points based on foosball rods
pts = np.array([
    (2, 400, 350),
    (0, 50, 100),
	(3, 550, 300),
    (1, 200, 400),
    (2, 400, 450),
	(3, 550, 500),
    (0, 50, 250),
    (2, 400, 250),
    (1, 200, 200),
	(3, 550, 100),
    (0, 50, 10),
    (2, 400, 150),
    (2, 400, 50)
])

print(pts)

# Sort by column 2, then by column 1
pts = pts[pts[:,2].argsort(kind='mergesort')]
pts = pts[pts[:,1].argsort(kind='mergesort')]

print("Sorted")
print(pts)
