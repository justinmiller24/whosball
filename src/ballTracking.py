# USAGE
# python ballTracking.py --video test-video.mp4
# python ballTracking.py --picamera 1
# python ballTracking.py

# import the necessary packages
from collections import deque
from imutils.video import VideoStream
import argparse
import cv2
import datetime
import imutils
import numpy as np
import time

# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-p", "--picamera", type=int, default=-1, help="whether or not the Raspberry Pi camera should be used")
ap.add_argument("-v", "--video", help="path to the (optional) video file")
ap.add_argument("-b", "--buffer", type=int, default=30, help="max buffer size")
ap.add_argument("--ballLower1", help="min HSV values lower1")
ap.add_argument("--ballUpper1", help="max HSV values upper1")
ap.add_argument("--ballLower2", help="min HSV values lower2")
ap.add_argument("--ballUpper2", help="max HSV values upper2")
args = vars(ap.parse_args())

# Define HSV bounds for foosball
ballLower1 = (0, 20, 30)
ballUpper1 = (5, 255, 255)
ballLower2 = (175, 20, 30)
ballUpper2 = (180, 255, 255)

ballLower1 = args.get("ballLower1") if args.get("ballLower1", False) else ballLower1
ballUpper1 = args.get("ballUpper1") if args.get("ballUpper1", False) else ballUpper1
ballLower2 = args.get("ballLower2") if args.get("ballLower2", False) else ballLower2
ballUpper2 = args.get("ballUpper2") if args.get("ballUpper2", False) else ballUpper2

print(ballLower1)
print(ballUpper1)
print(ballLower2)
print(ballUpper2)


# Initialize list of tracked points
pts = deque(maxlen=args["buffer"])

# if a video path was not supplied, grab the reference
# to the webcam
if not args.get("video", False):
	#vs = VideoStream(src=0).start()
	vs = VideoStream(usePiCamera=args["picamera"] > 0).start()

# otherwise, grab a reference to the video file
else:
	vs = cv2.VideoCapture(args["video"])

# allow the camera or video file to warm up
print("Warming up camera or video file")
time.sleep(2.0)

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

	# Resize, blur it, and convert to HSV
	frame = imutils.resize(frame, width=600)
	origImg = frame.copy()

	# Blur image
	blurred = cv2.GaussianBlur(origImg, (11, 11), 0)
	hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

	# Detect edges
	#edge = cv2.Canny(origImg, 100, 200)

	# Create "red" color mask, perform erosions and dilation to remove small blobs in mask
	mask1 = cv2.inRange(hsv, ballLower1, ballUpper1)
	mask2 = cv2.inRange(hsv, ballLower2, ballUpper2)
	mask_pre = cv2.bitwise_or(mask1, mask2)
	mask = cv2.erode(mask_pre, None, iterations=2)
	mask = cv2.dilate(mask, None, iterations=2)

	# Find contours in mask and initialize the current center (x, y) of the ball
	cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
	cnts = imutils.grab_contours(cnts)
	center = None

	# Ensure at least one contour was found
	if len(cnts) > 0:

		# find the largest contour in the mask, then use
		# it to compute the minimum enclosing circle and
		# centroid
		c = max(cnts, key=cv2.contourArea)
		((x, y), radius) = cv2.minEnclosingCircle(c)
		M = cv2.moments(c)
		center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
		print("Center:", center,  " Radius:", radius)

		# only proceed if the radius meets a minimum size
		if radius > 10:
			# draw the circle and centroid on the frame,
			# then update the list of tracked points
			cv2.circle(frame, (int(x), int(y)), int(radius), (0, 255, 255), 2)
			cv2.circle(frame, center, 5, (0, 0, 255), -1)

	# update the points queue
	pts.appendleft(center)

	# loop over the set of tracked points
	for i in range(1, len(pts)):
		# if either of the tracked points are None, ignore
		# them
		if pts[i - 1] is None or pts[i] is None:
			continue

		# otherwise, compute the thickness of the line and
		# draw the connecting lines
		thickness = int(np.sqrt(args["buffer"] / float(i + 1)) * 2.5)
		cv2.line(frame, pts[i - 1], pts[i], (0, 0, 255), thickness)

	# construct the final output frame, storing the original frame
	# at the top-left, the red channel in the top-right, the green
	# channel in the bottom-right, and the blue channel in the
	# bottom-left
	#(h, w) = frame.shape[:2]
	#output = np.zeros((h * 2, w * 2, 3), dtype="uint8")
	#output[0:h, 0:w] = origImg
	#output[0:h, w:w * 2] = blurred
	#output[h:h * 2, w:w * 2] = hsv
	#output[h:h * 2, 0:w] = frame
	# write the output frame to file
#	writer.write(output)


	# show the frame to our screen
	#cv2.imshow("Frame", frame)
	cv2.namedWindow("mask")
	cv2.moveWindow("mask", 100, 100)
	cv2.imshow("mask", mask_pre)

	#edge2 = np.reshape(edge, edge.shape + (1,))
	#cv2.imshow("Edges", edge2)

	# Create a table showing input image, mask, and output

	#mask_pre = mask_pre.reshape((mask_pre.shape[0], mask_pre.shape[1], 1))
    #mask2 = np.stack((mask,)*3, axis=-1)
	#print("Size: ", origImg.ndim, mask_pre.ndim, frame.ndim)
	#print(mask_pre)
	#break


	output = np.concatenate((origImg, frame), axis=1)
	cv2.namedWindow("Output")
	cv2.moveWindow("Output", 100, 600)
	cv2.imshow("Output", output)

	key = cv2.waitKey(1) & 0xFF

	# TODO: save the frame to our video output
	# https://www.pyimagesearch.com/2016/02/22/writing-to-video-with-opencv/

	# if the 'q' key is pressed, stop the loop
	if key == ord("q"):
		break

# if we are not using a video file, stop the camera video stream
if not args.get("video", False):
	vs.stop()

# otherwise, release the camera
else:
	vs.release()

# close all windows
cv2.destroyAllWindows()
