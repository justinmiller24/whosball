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
#import foosball
import motor


#def auto_canny(image, sigma=0.33):
	# compute the median of the single channel pixel intensities
	#v = np.median(image)
	# apply automatic Canny edge detection using the computed median
	#lower = int(max(0, (1.0 - sigma) * v))
	#upper = int(min(255, (1.0 + sigma) * v))
	#edged = cv2.Canny(image, lower, upper)
	# return the edged image
	#return edged

display.out("Starting Main Script")


# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-d", "--debug", type=int, default=0, help="whether or not to show debug mode")
ap.add_argument("-s", "--display", type=int, default=1, help="whether or not to display output")
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

# Globals
# Define Table Size
table_dim_cm = (56 * 2.54, 29 * 2.54)
# Debug Mode
debugMode = args["debug"] > 0
# Initialize list of tracked points
pts = deque(maxlen=30)
# Initialize ball position array
ball_position_history = []


# Initialize camera or video stream
vs = videoStream(debugMode, args["picamera"] > 0, args["video"], args["output"]).start()

# Setup game
#f = foosball().start()

# keep looping
while True:

	# Read next frame. If no frame exists, then we've reached the end of the video.
	frame = vs.getNextFrame()
	if frame is None:
		if debugMode:
			display.out("No frame exists, reached end of file")
		break

	origImg = frame.copy()

	# Grab image dimensions and determine center point
	(h, w) = origImg.shape[:2]
	#display.out(h)
	#display.out(w)
	(cX, cY) = (w // 2, h // 2)

	# Perspective transform
	#coords = np.array([(50, 125), (50, h-62), (w-65, 125), (w-65, h-62)])
	#coords = np.array([(0,0), (0,480), (640,0), (640,480)])
	#coords = np.array([(50+0,115+0), (50,115+297), (50+510,115+0), (50+510,115+297)])
	tL = (73,130)
	bL = (59,405)
	tR = (557,136)
	bR = (561,414)
	coords = np.array([tL, bL, tR, bR])

	# Show transformation coordinates on original image
	for (x, y) in coords:
		cv2.circle(origImg, (x, y), 5, (0, 255, 0), -1)

	croppedImg = vs.perspectiveTransform(coords)

	(h2, w2) = croppedImg.shape[:2]
	if debugMode:
		display.out("Dimensions:")
		display.out(h2)
		display.out(w2)
	finalImg = croppedImg.copy()

	# Detect foosball and players
	detection.detectFoosball()

	# HSV, Grayscale, Edges
	hsv = vs.getHSVImage()
	gray = vs.getGrayscale()
	gray3 = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
	#edge = cv2.Canny(origImg, 100, 200)

	# Canny edge detection
	# apply Canny edge detection using a wide threshold, tight
	# threshold, and automatically determined threshold
	#blurred = cv2.GaussianBlur(gray, (3, 3), 0)
	#wide = cv2.Canny(blurred, 10, 200)
	#tight = cv2.Canny(blurred, 225, 250)
	#canny = auto_canny(blurred)
	#canny3 = cv2.cvtColor(canny, cv2.COLOR_GRAY2BGR)

	# Blob detection
	# Set our filtering parameters
	# Initialize parameter settiing using cv2.SimpleBlobDetector
	blobImg = hsv.copy()
	params = cv2.SimpleBlobDetector_Params()

	# Set Area filtering parameters
	params.filterByArea = True
	params.minArea = 100

	# Set Circularity filtering parameters
	params.filterByCircularity = True
	params.minCircularity = 0.9

	# Set Convexity filtering parameters
	params.filterByConvexity = True
	params.minConvexity = 0.2

	# Set inertia filtering parameters
	params.filterByInertia = True
	params.minInertiaRatio = 0.01

	# Create a detector with the parameters
	detector = cv2.SimpleBlobDetector_create(params)

	# Detect blobs
	keypoints = detector.detect(blobImg)

	# Draw blobs on our image as red circles
	blank = np.zeros((1, 1))
	blobs = cv2.drawKeypoints(blobImg, keypoints, blank, (0, 0, 255), cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)

	number_of_blobs = len(keypoints)
	text = "Number of Circular Blobs: " + str(len(keypoints))
	cv2.putText(blobs, text, (20, 550), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 100, 255), 2)

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
		#if debugMode:
			#display.out("Circles is not None")

		# convert the (x, y) coordinates and radius of the circles to integers
		#circles = np.round(circles[0, :]).astype("int")
		#if debugMode:
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

		# Add to list of tracked points
		ball_position_history.append(center)
		if len(ball_position_history) > 1:

			# Last ball position
			lastPosition = ball_position_history[-2:][0]
			origX = lastPosition[0]
			origY = lastPosition[1]

			# Current ball position
			currPosition = ball_position_history[-1:][0]
			destX = currPosition[0]
			destY = currPosition[1]

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
		cv2.circle(finalImg, center, 5, (0, 0, 255), -1)

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
		cv2.line(finalImg, pts[i - 1], pts[i], (0, 0, 255), thickness)


	# Detect players
	#detection.detectPlayers()

	# Check for score
	#detection.detectScore()

	# Determine move, if any, and move linear and rotational motors
	#motor.determineMove()
	#motor.move()

	# Build multi view display and show on screen
	velocity = None
	output = display.update((croppedImg, gray3, mask3, finalImg), center, radius, distance, degrees, velocity)

	# Write frame to video output file
	if args["output"]:
		vs.write(output)

	# View output on screen/display
	if args["display"]:
		cv2.namedWindow("Original")
		cv2.moveWindow("Original", 1250, 100)
		cv2.imshow("Original", origImg)

		cv2.imshow("Output", output)
		# Handle user input
		# if the 'q' key is pressed, stop the loop
		if display.detectUserInput():
			break


# Stop video/camera feed and output writer
vs.stop()

# close all windows
cv2.destroyAllWindows()
