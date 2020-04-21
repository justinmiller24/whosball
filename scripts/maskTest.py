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


mask = np.zeros((h, w, 3), dtype="uint8")
#mask = np.ones((h, w, 3), dtype="uint8")
mask = cv2.bitwise_not(mask)

#mask[cv2.Range(0, mask.rows), cv2.Range(0, 9 * mask.cols / 240 )] = 0
cv2.rectangle(mask, (0, 0), (int(w * 9 / 240), h), (0, 0, 0), -1)
#mask[cv2.Range(0, mask.rows / 3), cv2.Range( 9 * mask.cols / 240 , 33 * mask.cols / 240)] = 0
#mask[cv2.Range(41 * mask.rows / 60, mask.rows), cv2.Range( 9 * mask.cols / 240,  33 * mask.cols / 240)] = 0
#mask[cv2.Range(0, mask.rows), cv2.Range(33 * mask.cols / 240, mask.cols / 6)] = 0
cv2.rectangle(mask, (int(w * 33 / 240), 0), (int(w * 40 / 240), h), (0, 0, 0), -1)
#mask[cv2.Range(0, mask.rows), cv2.Range(mask.cols / 4, 9 * mask.cols / 24)] = 0
cv2.rectangle(mask, (int(w * 60 / 240), 0), (int(w * 90 / 240), h), (0, 0, 0), -1)
#mask[cv2.Range(0, mask.rows), cv2.Range(29 * mask.cols / 60, 73 * mask.cols / 120)] = 0
cv2.rectangle(mask, (int(w * 116 / 240), 0), (int(w * 146 / 240), h), (0, 0, 0), -1)
#mask[cv2.Range(0, mask.rows), cv2.Range(3 * mask.cols / 4, mask.cols)] = 0
cv2.rectangle(mask, (int(w * 180 / 240), 0), (w, h), (0, 0, 0), -1)


#mask1 = cv2.inRange(self.hsv, self.dim["foosballMin1HSV"], self.dim["foosballMax1HSV"])
#mask2 = cv2.inRange(self.hsv, self.dim["foosballMin2HSV"], self.dim["foosballMax2HSV"])
#mask = cv2.bitwise_or(mask1, mask2)
#mask = cv2.erode(mask, None, iterations=2)
#mask = cv2.dilate(mask, None, iterations=2)
#self.mask3 = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)


# Show display until a key is pressed
#print(mask)

#mask3 = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
cv2.imshow("Mask", mask)
cv2.waitKey(0)


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
	# grab the frame from the stream
	origFrame = f.array
	#frame_HSV = cv.cvtColor(frame, cv.COLOR_BGR2HSV)

	# Crop image to just the foosball table
	tL = (73,130)
	tR = (557,136)
	bR = (561,414)
	bL = (59,405)
	origCoords = np.array([tL, tR, bR, bL], dtype="float32")

	w = 960
	h = 640
	finalCoords = np.array([(0,0), (w-1,0), (w-1,h-1), (0,h-1)], dtype="float32")
	M = cv2.getPerspectiveTransform(origCoords, finalCoords)
	frame = cv2.warpPerspective(origFrame, M, (w, h))

	# display frame to our screen
	# wait for keypress
	cv2.imshow("Frame", frame)
	cv2.waitKey(0)


	#src2 = cv2.imread('data/src/horse_r.png')
	mask2 = cv2.resize(mask, mask.shape[1::-1])

	print(mask2.shape)
	# (225, 400, 3)
	print(mask2.dtype)
	# uint8

	output = cv2.bitwise_and(frame, mask2)
	#cv2.imwrite('data/dst/opencv_bitwise_and.jpg', dst)

	# display frame to our screen
	# wait for keypress
	cv2.imshow("Output", output)
	cv2.waitKey(0)

	# clear the stream in preparation for the next frame
	rawCapture.truncate(0)

	# break when "q" key is pressed
	#if key == ord("q"):
		#break


# do a bit of cleanup
cv2.destroyAllWindows()
stream.close()
rawCapture.close()
camera.close()
