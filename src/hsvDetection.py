# USAGE
# python hsvDetection.py

# import the necessary packages
from collections import deque
from imutils.video import VideoStream
import cv2
import datetime
import imutils
import numpy as np
import time


vs = VideoStream(usePiCamera=True).start()

# allow the camera or video file to warm up
print("Warming up camera or video file")
time.sleep(2.0)

# keep looping
while True:
	# grab the current frame
	frame = vs.read()

	# handle the frame from VideoCapture or VideoStream
	frame = frame[1]

	# Find center
	#x = int(frame.shape[1] / 2)
	#y = int(frame.shape[0] / 2)

	# Resize image
	#frame = imutils.resize(frame, width=600)

	# Convert to HSV
	#print('Convert to HSV')
	#hsv_img = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
	print('Determine height and width of image')
	(h, w) = frame.shape[:2]
	#print [h, w, int(h/2), int(w/2)]
	#center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
	print("Center: ", (h, w))
	#centerPX = mask[int(h/2), int(w/2)]
    #print centerPX

	# Crop image
	#cropped = image[70:170, 440:540]
	#cv2.imshow("cropped", cropped)

	# Resize, blur it, and convert to HSV
	#frame = imutils.resize(frame, width=600)
	#blurred = cv2.GaussianBlur(frame, (11, 11), 0)
	#hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

	# Create "red" color mask, perform erosions and dilation to remove small blobs in mask
	#mask = cv2.inRange(hsv, ballLower, ballUpper)
	#mask = cv2.erode(mask, None, iterations=2)
	#mask = cv2.dilate(mask, None, iterations=2)

	# Find contours in mask and initialize the current center (x, y) of the ball
	#cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
	#cnts = imutils.grab_contours(cnts)
	#center = None

	# show the frame to our screen
	cv2.imshow("Frame", frame)
	key = cv2.waitKey(1) & 0xFF

	# if the 'q' key is pressed, stop the loop
	if key == ord("q"):
		break

# stop the camera video stream
vs.release()

# close all windows
cv2.destroyAllWindows()
