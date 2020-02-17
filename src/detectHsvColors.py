# import the necessary packages
from picamera.array import PiRGBArray
from picamera import PiCamera
import time
import cv2

# initialize the camera and grab a reference to the raw camera capture
camera = PiCamera()
camera.resolution = (640, 480)
camera.framerate = 32
rawCapture = PiRGBArray(camera, size=(640, 480))

# allow the camera to warmup
time.sleep(0.1)

# capture frames from the camera
for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):

	# Convert to NumPy array
	img = frame.array

	# Convert to grayscale
	gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

	# Convert to HSV
	hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

	# Find center and draw circle
	w = int(img.shape[1] / 2)
	h = int(img.shape[0] / 2)
	cv2.circle(img, (w, h), 5, (0, 255, 255), 5)
	#cv2.circle(img, (w, h), 5, (0, 0, 255), -1)

	# Show the frame
	cv2.imshow("Frame", img)
	key = cv2.waitKey(1) & 0xFF

	#print(type(img))
	#print('RGB shape: ', img.shape)        # Rows, cols, channels
	#print('img.dtype: ', img.dtype)
	#print('img.size: ', img.size)
	#print("Center: ", (w, h))
	#print("BGR Value of center: ", img[h, w])
	#print("Grayscale Value of center: ", gray[h, w])
	print("HSV Value of center: ", hsv[h, w])

	# clear the stream in preparation for the next frame
	rawCapture.truncate(0)

	# if the `q` key was pressed, break from the loop
	if key == ord("q"):
		break
