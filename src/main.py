#########################
# Automated Foosball    #
#########################

# USAGE
# python main.py
# python main.py --picamera 1
# python main.py --video test-video.mp4
# python main.py --video input-video.mp4 --output output-video.mp4

# import the necessary packages
from __future__ import print_function
from collections import deque
import argparse
import cv2
import imutils
import math
import numpy as np

from video import videoStream
import detection
import display
import motor


display.out("Starting Main Script")


# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-d", "--display", type=int, default=1, help="whether or not to display output")
ap.add_argument("-p", "--picamera", type=int, default=0, help="whether or not the Raspberry Pi camera should be used")
ap.add_argument("-v", "--video", help="path to the (optional) video file")
ap.add_argument("-o", "--output", help="path to output video file")
args = vars(ap.parse_args())

# Define HSV bounds for foosball
#ballMinHSV = (174, 155, 205)
#ballMaxHSV = (176, 180, 240)
ballMin1HSV = (0, 20, 20)
ballMax1HSV = (10, 255, 255)
ballMin2HSV = (170, 20, 20)
ballMax2HSV = (180, 255, 255)

# Define Table Size
table_dim_cm = (56 * 2.54, 29 * 2.54)

# Initialize list of tracked points
pts = deque(maxlen=30)

# Initialize ball position array
ball_position_history = []


# Initialize camera or video stream
vs = videoStream(args["picamera"] > 0, args["video"], args["output"]).start()


# keep looping
while True:

	# Read next frame. If no frame exists, then we've reached the end of the video.
	frame = vs.getNextFrame()
	if frame is None:
		display.out("No frame exists, reached end of file")
		break

	(h, w) = frame.shape[:2]
	origImg = frame.copy()

	# Detect foosball and players
	detection.detectBall()

	# HSV, Grayscale, Edges
	hsv = vs.getHSVImage()
	gray = vs.getGrayscale()
	gray3 = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
	#edge = cv2.Canny(origImg, 100, 200)

	# Create color mask for foosball and perform erosions and dilation to remove small blobs in mask
	mask1 = cv2.inRange(hsv, ballMin1HSV, ballMax1HSV)
	mask2 = cv2.inRange(hsv, ballMin2HSV, ballMax2HSV)
	mask = cv2.bitwise_or(mask1, mask2)
	mask = cv2.erode(mask, None, iterations=2)
	mask = cv2.dilate(mask, None, iterations=2)
	mask3 = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)

	# Detect HoughCircles
	# detect circles in the image
	#houghImg = np.zeros((h, w, 3), dtype="uint8")
	#circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, 1.2, 100)
	#circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, 1.0, 45, 75, 40, 20, 40);
	#hough1 = mask3.copy()
	#houghGray = cv2.cvtColor(hough1, cv2.COLOR_BGR2GRAY)
	#circles = cv2.HoughCircles(houghGray, cv2.HOUGH_GRADIENT, 1.0, 45, 75, 40, 20, 40);

	# ensure at least some circles were found
	#if circles is not None:
		#display.out("Circles is not None")

		# convert the (x, y) coordinates and radius of the circles to integers
		#circles = np.round(circles[0, :]).astype("int")
		#display.out(circles)

		# loop over the (x, y) coordinates and radius of the circles
		#for (x, y, r) in circles:

			# draw the circle in the output image, then draw a rectangle
			# corresponding to the center of the circle
			#cv2.circle(houghImg, (x, y), r, (0, 0, 255), 4)
			#cv2.rectangle(houghImg, (x - 5, y - 5), (x + 5, y + 5), (0, 128, 255), -1)

	# Find contours in mask and initialize the current center (x, y) of the ball
	cnts = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
	# Extract contours depending on OpenCV version
	#cnts = cnts[0] if len(cnts) == 2 else cnts[1]
	cnts = imutils.grab_contours(cnts)

	# Iterate through contours and filter by the number of vertices
	cntsImg = np.zeros((h, w, 3), dtype="uint8")
	for c in cnts:
		perimeter = cv2.arcLength(c, True)
		approx = cv2.approxPolyDP(c, 0.04 * perimeter, True)
		if len(approx) > 5:
			cv2.drawContours(cntsImg, [c], -1, (36, 255, 12), -1)

	center = None
	radius = None
	distance = None
	degrees = None
	velocity = None

	# Ensure at least one contour was found
	if len(cnts) > 0:

		# Find the largest contour in the mask and use this to
		# compute the minimum enclosing circle and centroid
		c = max(cnts, key=cv2.contourArea)
		((x, y), radius) = cv2.minEnclosingCircle(c)
		M = cv2.moments(c)
		center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
		#display.out("Center: {}".format(center))

		# Add to list of tracked points
		ball_position_history.append(center)
		if len(ball_position_history) > 1:

			# Last ball position
			#display.out(ball_position_history)
			lastPosition = ball_position_history[-2:][0]
			origX = lastPosition[0]
			origY = lastPosition[1]

			# Current ball position
			currPosition = ball_position_history[-1:][0]
			destX = currPosition[0]
			destY = currPosition[1]
			#display.out("Last Position: {} Current Position: {}".format(lastPosition, currPosition))
			#display.out("OrigX: {} OrigY: {} DestX: {} DestY: {}".format(origX, origY, destX, destY))

			# Deltas
			deltaX = destX - origX
			deltaY = destY - origY

			# Distance
			distancePX = math.sqrt(deltaX * deltaX + deltaY * deltaY)
			#distanceCM = distancePX / ratio_pxcm
			#distanceM = distanceCM / 100
			distance = distancePX

			# Velocity
			#velocity = distance / frame_time

			# Direction
			# Calculate number degrees between two points
			# Calculate arc tangent (in radians) and convert to degrees
			degrees_temp = math.atan2(deltaX, deltaY) / math.pi * 180
			if degrees_temp < 0:
				degrees = 360 + degrees_temp
			else:
				degrees = degrees_temp

		# Draw centroid
		cv2.circle(frame, center, 5, (0, 0, 255), -1)

	# Update list of tracked points
	pts.appendleft(center)

	# loop over the set of tracked points
	for i in range(1, len(pts)):
		# if either of the tracked points are None, ignore them
		if pts[i - 1] is None or pts[i] is None:
			continue

		# otherwise, compute the thickness of the line and draw the connecting lines
		bufferLength = 30
		thickness = int(np.sqrt(bufferLength / float(i + 1)) * 2.5)
		cv2.line(frame, pts[i - 1], pts[i], (0, 0, 255), thickness)



	detection.detectPlayers()

	# Check for score
	detection.detectScore()

	# Determine move, if any, and move linear and rotational motors
	motor.determineMove()
	motor.move()

	# Build multi view display and show on screen
	velocity = None
	output = display.update((origImg, cntsImg, mask3, frame), center, radius, distance, degrees, velocity)

	# Write frame to video output file
	if args["output"]:
		vs.write(output)

	# View output on screen/display
	if args["display"]:
		cv2.imshow("Output", output)
		# Handle user input
		# if the 'q' key is pressed, stop the loop
		if display.detectUserInput():
			break


# Stop video/camera feed and output writer
vs.stop()

# close all windows
cv2.destroyAllWindows()
