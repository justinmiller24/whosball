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


#cv::Mat mask = cv::Mat::zeros( size, CV_8UC1 );
mask = cv2.zeros(camera.resolution, cv2.CV_8UC1)
#bitwise_not(mask, mask);
mask = cv2.bitwise_not(mask)

mask(cv2.Range(0, mask.rows), cv2.Range(0, 9 * mask.cols / 240 )) = 0
mask(cv2.Range(0, mask.rows / 3), cv2.Range( 9 * mask.cols / 240 , 33 * mask.cols / 240)) = 0
mask(cv2.Range(41 * mask.rows / 60, mask.rows), cv2.Range( 9 * mask.cols / 240,  33 * mask.cols / 240)) = 0
mask(cv2.Range(0, mask.rows), cv2.Range(33 * mask.cols / 240, mask.cols / 6)) = 0
mask(cv2.Range(0, mask.rows), cv2.Range(mask.cols / 4, 9 * mask.cols / 24)) = 0
mask(cv2.Range(0, mask.rows), cv2.Range(29 * mask.cols / 60, 73 * mask.cols / 120)) = 0
mask(cv2.Range(0, mask.rows), cv2.Range(3 * mask.cols / 4, mask.cols)) = 0

# Show display until a key is pressed
mask3 = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
cv2.imshow("Mask", mask3)
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
	frame = f.array
	#frame_HSV = cv.cvtColor(frame, cv.COLOR_BGR2HSV)

	# display frame to our screen
	cv2.imshow("Frame", frame)
	key = cv2.waitKey(1) & 0xFF

	# clear the stream in preparation for the next frame
	rawCapture.truncate(0)

	# break when "q" key is pressed
	if key == ord("q"):
		break


# do a bit of cleanup
cv2.destroyAllWindows()
stream.close()
rawCapture.close()
camera.close()
