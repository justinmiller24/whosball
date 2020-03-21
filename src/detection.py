from imutils.video import VideoStream
import imutils
import math
import numpy as np


# Define HSV bounds for foosball
ballMinHSV = (174, 155, 205)
ballMaxHSV = (176, 180, 240)


def init():

    # Initialize list of tracked points
    pts = deque(maxlen=args["buffer"])

    # Initialize ball position array
    ball_position_history = []


def getFrame(useVideoStream):

	# grab the current frame
	frame = vs.read()

	# handle the frame from VideoCapture or VideoStream
	frame = frame[1] if useVideoStream else frame

	# if we are viewing a video and we did not grab a frame,
	# then we have reached the end of the video
	if frame is None:
		print("End of file")
		break


def detectBall(outputFile=None):
    print("Detect Foosball")

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
        buffer = 30
		thickness = int(np.sqrt(buffer / float(i + 1)) * 2.5)
		cv2.line(frame, pts[i - 1], pts[i], (0, 0, 255), thickness)

	# Build multi view display and show on screen
	velocity = None
	output = gui.updateDisplay((origImg, gray3, mask3, frame), center, radius, distance, degrees, velocity)
	cv2.imshow("Output", output)

    # Write to output file
	if outputFile:
		# check if the writer is None
		if writer is None:
			writer = cv2.VideoWriter(args["output"], fourcc, 30, (mvWidth, mvHeight), True)

		# write the output frame to file
		writer.write(output)


def detectPlayers():
	print("Detect RED and BLUE players")


def detectScore():
    print("Check to see if a score occurred")
