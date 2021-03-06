###########################
# Generate ArUco markers  #
###########################

# This script is used to generate an ArUco marker tag and save it
# Created by Justin Miller on 4.13.2020

# USAGE:
# python3 generateArucoMarkers.py
# python3 generateArucoMarkers.py --rows 4 --columns 3
# python3 generateArucoMarkers.py --rows 4 --columns 3 --save

# Import packages
import argparse
import cv2.aruco as aruco
import matplotlib as mpl
import matplotlib.pyplot as plt

# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-r", "--rows", type=int, default=2, help="Number of rows to generate")
ap.add_argument("-c", "--columns", type=int, default=2, help="Number of columns to generate")
ap.add_argument("-s", "--save", help="Save output to file", action="store_true")
args = vars(ap.parse_args())

arucoDict = aruco.Dictionary_get(aruco.DICT_4X4_50)
#print(arucoDict)

fig = plt.figure()
for i in range(0, args["columns"] * args["rows"]):
	ax = fig.add_subplot(args["rows"], args["columns"], i + 1)
	# Draw ArUco marker
	# The second parameter is the ID number, the third parameter is the total image size
	img = aruco.drawMarker(arucoDict, i, 100)
	plt.imshow(img, cmap = mpl.cm.gray, interpolation = "nearest")
	ax.axis("off")

# Save output file or show output
if args["save"]:
	plt.savefig("arucoOutput.png")
else:
	plt.show()
