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
import datetime
import math
import numpy as np

from video import videoStream
import detection
import gui
import motor

# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-d", "--display", type=int, default=1, help="whether or not to display output")
ap.add_argument("-p", "--picamera", type=int, default=-1, help="whether or not the Raspberry Pi camera should be used")
ap.add_argument("-v", "--video", help="path to the (optional) video file")
ap.add_argument("-o", "--output", help="path to output video file")
args = vars(ap.parse_args())

# Define HSV bounds for foosball
ballMinHSV = (174, 155, 205)
ballMaxHSV = (176, 180, 240)

# Define Table Size
table_dim_cm = (56 * 2.54, 29 * 2.54)

# Initialize list of tracked points
pts = deque(maxlen=30)

# Initialize ball position array
ball_position_history = []


# Initialize camera
vs = videoStream(args["picamera"] > 0, args["video"])
vs.start()


# Define the codec and create VideoWriter object
outputFile = True if args.get("output", False) else False
if outputFile:
	print("Recording to file:", args["output"])
	fourcc = cv2.VideoWriter_fourcc('M','J','P','G')
	writer = None

# keep looping
while True:

	# Read next frame. If no frame exists, then we've reached the end of the video.
	frame = video.getNextFrame()
	if frame is None:
		print("No frame exists, reached end of file")
		break

    (h, w) = frame.shape[:2]
    origImg = frame.copy()

	# Detect foosball and players
	detection.detectBall()

	# HSV, Grayscale, Edges
	hsv = video.getHSVImage()
	gray3 = video.getGrayscale()
	#edge = cv2.Canny(origImg, 100, 200)

	# Create color mask for foosball and perform erosions and dilation to remove small blobs in mask
	mask = cv2.inRange(hsv, ballMinHSV, ballMaxHSV)
	mask = cv2.erode(mask, None, iterations=2)
	mask = cv2.dilate(mask, None, iterations=2)
	mask3 = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)

	# Find contours in mask and initialize the current center (x, y) of the ball
	cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
	cnts = imutils.grab_contours(cnts)
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
		#print("Center: {}".format(center))

		# Add to list of tracked points
		ball_position_history.append(center)
		if len(ball_position_history) > 1:

			# Last ball position
			#print(ball_position_history)
			lastPosition = ball_position_history[-2:][0]
			origX = lastPosition[0]
			origY = lastPosition[1]

			# Current ball position
			currPosition = ball_position_history[-1:][0]
			destX = currPosition[0]
			destY = currPosition[1]
			#print("Last Position: {} Current Position: {}".format(lastPosition, currPosition))
			#print("OrigX: {} OrigY: {} DestX: {} DestY: {}".format(origX, origY, destX, destY))

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
		thickness = int(np.sqrt(args["buffer"] / float(i + 1)) * 2.5)
		cv2.line(frame, pts[i - 1], pts[i], (0, 0, 255), thickness)



	detection.detectPlayers()

	# Check for score
	detection.detectScore()

	# Determine move, if any, and move linear and rotational motors
	motors.determineMove()
	motors.move()

	velocity = None
	# Build multi view display and show on screen
	output = gui.updateDisplay((origImg, gray3, mask3, frame), center, radius, distance, degrees, velocity)

	# View output on screen/display
	if args["display"]:
		cv2.imshow("Output", output)

	# Save output to video file
	if outputFile:
		# check if the writer is None
		if writer is None:
			writer = cv2.VideoWriter(args["output"], fourcc, 30, (mvWidth, mvHeight), True)

		# write the output frame to file
		writer.write(output)


	# Handle user input
	# if the 'q' key is pressed, stop the loop
	if gui.detectUserInput():
		break

# Stop video stream or camera feed
vs.stop()

# Stop recording video file
if outputFile:
	writer.release()

# close all windows
cv2.destroyAllWindows()
