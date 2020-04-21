#
# This script is used to create a mask for RED and BLUE players
# Created by Justin Miller on 3.16.2020
#
# USAGE:
# python3 maskTest.py


# import the necessary packages
from picamera.array import PiRGBArray
from picamera import PiCamera
import cv2
import numpy as np
import time


w = 640
h = 480

# Create "mask" for RED foosball player
mask = np.zeros((h, w, 3), dtype="uint8")
mask = cv2.bitwise_not(mask)
#mask = np.ones((h, w, 3), dtype="uint8")
cv2.rectangle(mask, (0, 0), (int(w * 9 / 240), h), (0, 0, 0), -1)
cv2.rectangle(mask, (int(w * 33 / 240), 0), (int(w * 40 / 240), h), (0, 0, 0), -1)
cv2.rectangle(mask, (int(w * 60 / 240), 0), (int(w * 90 / 240), h), (0, 0, 0), -1)
cv2.rectangle(mask, (int(w * 116 / 240), 0), (int(w * 146 / 240), h), (0, 0, 0), -1)
cv2.rectangle(mask, (int(w * 180 / 240), 0), (w, h), (0, 0, 0), -1)

cv2.imshow("Mask", mask)

# initialize the camera and stream
camera = PiCamera()
camera.resolution = (640, 480)
camera.framerate = 32
rawCapture = PiRGBArray(camera, size=camera.resolution)
stream = camera.capture_continuous(rawCapture, format="bgr", use_video_port=True)

# allow the camera to warmup
time.sleep(2.0)

# loop over some frames
for (i, f) in enumerate(stream):

	# Grab latest frame from PiCamera stream
	origFrame = f.array
	#img1 = cv2.cvtColor(origFrame, cv2.COLOR_GRAY2BGR)

	# Apply homography to show just the foosball table
	# Crop image to just the foosball table
	tL = (73,130)
	tR = (557,136)
	bR = (561,414)
	bL = (59,405)
	origCoords = np.array([tL, tR, bR, bL], dtype="float32")
	finalCoords = np.array([(0,0), (w-1,0), (w-1,h-1), (0,h-1)], dtype="float32")
	M = cv2.getPerspectiveTransform(origCoords, finalCoords)
	frame = cv2.warpPerspective(origFrame, M, (w, h))

	mask2 = cv2.resize(mask, mask.shape[1::-1])
	#print(mask2.shape)
	# (225, 400, 3)
	#print(mask2.dtype)
	# uint8


	#img2 = contours_img

	# Create a mask of contours and create its inverse mask also
	#img2gray = cv2.cvtColor(img2,cv2.COLOR_BGR2GRAY)
	#ret, mask = cv2.threshold(img2gray, 10, 255, cv2.THRESH_BINARY)
	#mask_inv = cv2.bitwise_not(mask)

	# Now black-out the area of contours in original image
	#img1_bg = cv2.bitwise_and(img1, img1, mask = mask_inv)

	# Take only region of contours from contours image.
	#img2_fg = cv2.bitwise_and(img2, img2, mask = mask)

	# Put contours in image and modify the main image
	#dst = cv2.add(img1_bg,img2_fg)
	#cv2.imshow('res',dst)

	output = cv2.bitwise_and(frame, mask2)

	# Display output and wait for "q" keypress to break loop
	cv2.imshow("Output", np.hstack((mask, frame, output)))
	if cv2.waitKey(1) & 0xFF == ord("q"):
		break

	# clear the stream in preparation for the next frame
	rawCapture.truncate(0)


# do a bit of cleanup
cv2.destroyAllWindows()
stream.close()
rawCapture.close()
camera.close()
