#########################
# Automated Foosball    #
#########################

# USAGE
# python main.py
# python main.py --debug
# python main.py --picamera
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
from foosball import foosball


#def auto_canny(image, sigma=0.33):
	# compute the median of the single channel pixel intensities
	#v = np.median(image)
	# apply automatic Canny edge detection using the computed median
	#lower = int(max(0, (1.0 - sigma) * v))
	#upper = int(min(255, (1.0 + sigma) * v))
	#edged = cv2.Canny(image, lower, upper)
	# return the edged image
	#return edged

print("Starting Main Script")


# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-d", "--debug", help="whether or not to show debug mode", action="store_true")
ap.add_argument("-s", "--display", type=int, default=1, help="whether or not to display output")
ap.add_argument("-p", "--picamera", help="whether or not the Raspberry Pi camera should be used", action="store_true")
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

# Define coordinate bounds for foosball table
tL = (73,130)
bL = (59,405)
tR = (557,136)
bR = (561,414)
tableCoords = np.array([tL, bL, tR, bR])

# Globals
# Define Table Size
table_dim_cm = (56 * 2.54, 29 * 2.54)
# Initialize list of tracked points
pts = deque(maxlen=30)
# Initialize ball position array
ball_position_history = []


# Initialize camera or video stream
vs = videoStream(args["debug"], args["picamera"], args["video"], args["output"]).start()

# Setup game
foosball = foosball(args["debug"]).start()

# keep looping
while True:

	# Read next frame. If no frame exists, then we've reached the end of the video.
	frame = vs.getNextFrame()
	if frame is None:
		if args["debug"]:
			print("No frame exists, reached end of file")
		break

	# Save current frame
	foosball.setRawFrame(frame)

	# Transform perspective based on key points
	origImg = foosball.perspectiveTransform(tableCoords)

	tempImg = origImg.copy()

	# Detect foosball and players
	foosball.detectBall()

	# HSV, Grayscale, Edges
	blurred = cv2.GaussianBlur(tempImg, (11, 11), 0)
	hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
	gray = cv2.cvtColor(tempImg, cv2.COLOR_RGB2GRAY)
	gray3 = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

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
	#blobImg = hsv.copy()
	#params = cv2.SimpleBlobDetector_Params()

	# Set Area filtering parameters
	#params.filterByArea = True
	#params.minArea = 100

	# Set Circularity filtering parameters
	#params.filterByCircularity = True
	#params.minCircularity = 0.9

	# Set Convexity filtering parameters
	#params.filterByConvexity = True
	#params.minConvexity = 0.2

	# Set inertia filtering parameters
	#params.filterByInertia = True
	#params.minInertiaRatio = 0.01

	# Create a detector with the parameters
	#detector = cv2.SimpleBlobDetector_create(params)

	# Detect blobs
	#keypoints = detector.detect(blobImg)

	# Draw blobs on our image as red circles
	#blank = np.zeros((1, 1))
	#blobs = cv2.drawKeypoints(blobImg, keypoints, blank, (0, 0, 255), cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)

	#number_of_blobs = len(keypoints)
	#text = "Number of Circular Blobs: " + str(len(keypoints))
	#cv2.putText(blobs, text, (20, 550), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 100, 255), 2)

	# Create color mask for foosball and perform erosions and dilation to remove small blobs in mask
	mask1 = cv2.inRange(hsv, ballMin1HSV, ballMax1HSV)
	mask2 = cv2.inRange(hsv, ballMin2HSV, ballMax2HSV)
	mask = cv2.bitwise_or(mask1, mask2)
	mask = cv2.erode(mask, None, iterations=2)
	mask = cv2.dilate(mask, None, iterations=2)
	mask3 = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)

	# Find contours in mask and initialize the current center (x, y) of the ball
	cnts = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
	# Extract contours depending on OpenCV version
	cnts = imutils.grab_contours(cnts)

	# Iterate through contours and filter by the number of vertices
	(h, w) = origImg.shape[:2]
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
	#foosball.detectPlayers()

	# Check for goal and update score
	#foosball.checkForGoal()

	# Determine move, if any, and move linear and rotational motors
	#foosball.determineMotorMovement()
	#foosball.moveMotors()

	# Build multi view display and show on screen
	velocity = None
	output = foosball.updateDisplay((origImg, gray3, mask3, finalImg), center, radius, distance, degrees, velocity)

	# Write frame to video output file
	if args["output"]:
		vs.write(output)

	# View output on screen/display
	if args["display"]:

		# Display multiview output
		cv2.imshow("Output", output)

		# Display original (uncropped) image
		# Show transformation coordinates on original image
		for (x, y) in tableCoords:
			cv2.circle(frame, (x, y), 5, (0, 255, 0), -1)
		cv2.namedWindow("Raw")
		cv2.moveWindow("Raw", 1250, 100)
		cv2.imshow("Raw", frame)

		# Handle user input - stop the loop if the "q" key is pressed
		if cv2.waitKey(1) & 0xFF == ord("q"):
			break


# Stop video/camera feed and output writer
vs.stop()

# close all windows
cv2.destroyAllWindows()
