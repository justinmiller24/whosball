from imutils.video import VideoStream
import cv2
import imutils
import time


class videoStream:

    # Initialize video stream instance
    def __init__(self, usePiCamera=False, videoFile=None):

        # Initialize the camera and stream
        print("Initialize Camera")

        self.usePiCamera = usePiCamera
        self.videoFile = videoFile


    # Start stream
    def start(self):

        if self.videoFile is not None:
            self.stream = cv2.VideoCapture(self.videoFile)
        else:
            self.stream = VideoStream(usePiCamera=self.usePiCamera).start()

        # Allow camera or video file to warm up
        print("Warming up camera or video file")
        time.sleep(2.0)

        return self.stream


    # Get next frame from camera or video stream and resize
    def getNextFrame():
        print("Get Next Frame")
        self.frame = self.stream.read()
        self.frame = self.frame[1] if args.get("video", False) else self.frame

        if self.frame is not None:
            self.frame = imutils.resize(self.frame, width=600)

        return self.frame


    def getBlurredImage():
        print("Get blurred image")
        self.blurred = cv2.GaussianBlur(self.frame, (11, 11), 0)
        return self.blurred


    def getHSVImage():
        print("Get HSV image")
        self.hsv = cv2.cvtColor(self.blurred, cv2.COLOR_BGR2HSV)
        return self.hsv


    def getGrayscale():
        print("Get grayscale image")
        gray = cv2.cvtColor(self.frame, cv2.COLOR_RGB2GRAY)
        self.grayscale = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        return self.grayscale


    # Stop stream
    def stop(self):
        # if we are using a video file, stop the camera video stream
        if self.videoFile is not None:
            self.stream.stop()

        # otherwise, release the camera
        else:
            self.stream.release()
