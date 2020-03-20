#########################
# Automated Foosball    #
#########################

# USAGE
# python ballTracking.py
# python ballTracking.py --picamera 1
# python ballTracking.py --video test-video.mp4
# python ballTracking.py --video input-video.mp4 --output output-video.mp4

# import the necessary packages
from __future__ import print_function
from collections import deque
from imutils.video import VideoStream
import argparse
import cv2
import datetime
import imutils
import math
import numpy as np
import time

import detection
import foosball
import gui

# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-p", "--picamera", type=int, default=-1, help="whether or not the Raspberry Pi camera should be used")
ap.add_argument("-v", "--video", help="path to the (optional) video file")
ap.add_argument("-b", "--buffer", type=int, default=30, help="max buffer size")
ap.add_argument("-o", "--output", help="path to output video file")
args = vars(ap.parse_args())

# Define HSV bounds for foosball
ballMinHSV = (174, 155, 205)
ballMaxHSV = (176, 180, 240)

# Define Table Size
table_dim_cm = (56 * 2.54, 29 * 2.54)

# Initialize list of tracked points
pts = deque(maxlen=args["buffer"])

# Initialize ball position array
ball_position_history = []


# if a video path was not supplied, grab the reference to the webcam
# otherwise, grab a reference to the video file
if not args.get("video", False):
	#vs = VideoStream(src=0).start()
	vs = VideoStream(usePiCamera=args["picamera"] > 0).start()
else:
	vs = cv2.VideoCapture(args["video"])


# allow the camera or video file to warm up
print("Warming up camera or video file")
time.sleep(2.0)


# Define the codec and create VideoWriter object
outputFile = True if args.get("output", False) else False
if outputFile:
	print("Recording to file:", args["output"])
	fourcc = cv2.VideoWriter_fourcc('M','J','P','G')
	writer = None

# keep looping
while True:
	# grab the current frame
	frame = vs.read()

	# handle the frame from VideoCapture or VideoStream
	frame = frame[1] if args.get("video", False) else frame

	# if we are viewing a video and we did not grab a frame,
	# then we have reached the end of the video
	if frame is None:
		print("End of file")
		break

	# Main loop
	while gameInProgress:
		detection.detectBall()
		detection.detectPlayers()

		foosball.checkForScore()
		foosball.determineMotorMovement()
		foosball.moveMotors()

		# Update video display and handle user input
		gui.updateDisplay()
		if gui.detectUserInput():
			break





	// Calculate and show ball position and score
        scoreCounter.trackBallAndScore(foundBallsState.getCenter(), foundBallsState.getFoundball());

        // Display GUI elements and score board
        cv::copyMakeBorder(flippedFrame, flippedFrame, 45, 45, 5, 5, cv::BORDER_CONSTANT);
        gui::printScoreBoard(scoreCounter, flippedFrame, (int)(5.0 / 12 * config["gameTableWidth"].get<int>()), 30);
        gui::showCenterPosition(flippedFrame, foundBallsState.getCenter(), 10, config["gameTableHeight"].get<int>() + 65);
        gui::showStatistics(flippedFrame, founded, counter, 10, config["gameTableHeight"].get<int>() + 80);
	gui::printKeyDoc(flippedFrame, 300, config["gameTableHeight"].get<int>() + 65);
	cv::imshow("Foosball", flippedFrame);

	redPlayersFinder.clearVectors();
	bluePlayersFinder.clearVectors();
        foundBallsState.clearVectors();

	gui::handlePressedKeys(cv::waitKey(10), originalEnabled, trackingEnabled,
			       blueDetectionEnabled, redDetectionEnabled, pause, debugMode);
    }



	# Resize, blur it, and convert to HSV
	frame = imutils.resize(frame, width=600)
	(h, w) = frame.shape[:2]
	origImg = frame.copy()

	# Blurred
	blurred = cv2.GaussianBlur(origImg, (11, 11), 0)
	hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

	# Grayscale
	gray = cv2.cvtColor(origImg, cv2.COLOR_RGB2GRAY)
	gray3 = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

	# Edges
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

	# Build multi view display and show on screen
	velocity = None
	output = gui.getVideoDisplay((origImg, gray3, mask3, frame), center, radius, distance, degrees, velocity)
	cv2.imshow("Output", output)

	# Write to output file
	if outputFile:
		# check if the writer is None
		if writer is None:
			writer = cv2.VideoWriter(args["output"], fourcc, 30, (mvWidth, mvHeight), True)

		# write the output frame to file
		writer.write(output)

	# if the 'q' key is pressed, stop the loop
	key = cv2.waitKey(1) & 0xFF
	if key == ord("q"):
		break

# if we are not using a video file, stop the camera video stream
if not args.get("video", False):
	vs.stop()

# otherwise, release the camera
else:
	vs.release()

# Stop recording video file
if outputFile:
	writer.release()

# close all windows
cv2.destroyAllWindows()
