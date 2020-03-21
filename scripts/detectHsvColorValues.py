###########################
# Detect HSV Color Values #
###########################

# This script is used to detect HSV color values
# Created by Justin Miller on 2.14.2020

# USAGE:
# python3 detectHsvColorValues.py

# Import packages
from picamera.array import PiRGBArray
from picamera import PiCamera
import time
import cv2

# Initialize camera and grab a reference to the raw camera capture
camera = PiCamera()
camera.resolution = (640, 480)
camera.framerate = 32
rawCapture = PiRGBArray(camera, size=(640, 480))

# Let camera warm up
time.sleep(0.1)

# Capture frames from camera
for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):

	# Convert to NumPy array
	img = frame.array

	# Convert to grayscale
	gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

	# Convert to HSV
	hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

	# Find center
	w = int(img.shape[1] / 2)
	h = int(img.shape[0] / 2)

	# Draw circle
	cv2.circle(img, (w, h), 0, (0, 255, 255), 8)

	# Show the frame
	cv2.imshow("Frame", img)

	# Console log
	#print(type(img))
	#print('RGB shape: ', img.shape)        # Rows, cols, channels
	#print('img.dtype: ', img.dtype)
	#print('img.size: ', img.size)
	#print("Center: ", (w, h))
	#print("BGR Value of center: ", img[h, w])
	#print("Grayscale Value of center: ", gray[h, w])
	print("HSV Value of center: ", hsv[h, w])

	# Clear stream in preparation for next frame
	rawCapture.truncate(0)

	# Press `q` to break from loop
	key = cv2.waitKey(1) & 0xFF
	if key == ord("q"):
		break
