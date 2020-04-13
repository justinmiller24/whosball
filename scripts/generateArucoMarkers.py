###########################
# Generate ArUco markers  #
###########################

# This script is used to generate an ArUco marker tag and save it
# Created by Justin Miller on 4.13.2020

# USAGE:
# python3 generateArucoMarkers.py
# python3 generateArucoMarkers.py --rows 3 --columns 2
# python3 generateArucoMarkers.py --rows 3 --columns 2 --output outputFile.png

# Import packages
import argparse
import cv2.aruco as aruco
import matplotlib as mpl
import matplotlib.pyplot as plt

# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-r", "--rows", type=int, default=3, help="Number of rows to generate")
ap.add_argument("-c", "--columns", type=int, default=4, help="Number of columns to generate")
ap.add_argument("-o", "--output", default="output.png", help="Path to output file")
args = vars(ap.parse_args())

arucoDict = aruco.Dictionary_get(aruco.DICT_6X6_250)
print(arucoDict)

fig = plt.figure()
for i in range(1, args["columns"] * args["rows"] + 1):
	ax = fig.add_subplot(args["rows"], args["columns"], i)

	# Draw ArUco marker
	# The second parameter is the ID number
	# The third parameter is the total image size
	img = aruco.drawMarker(arucoDict, i, 700)

	plt.imshow(img, cmap = mpl.cm.gray, interpolation = "nearest")
	ax.axis("off")

plt.savefig(args["output"])
plt.show()
