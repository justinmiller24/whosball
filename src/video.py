from imutils.video import VideoStream
import cv2
import imutils
import time


class videoStream:

    # Initialize video stream instance
    def __init__(self, usePiCamera=False, videoFile=None, outputFile=None):

        # Initialize the camera and stream
        print("Initialize Camera")

        self.usePiCamera = usePiCamera
        self.videoFile = videoFile
        self.outputFile = outputFile
        self.writer = None


    # Start stream
    def start(self):

        if self.videoFile is not None:
            self.stream = cv2.VideoCapture(self.videoFile)
        else:
            self.stream = VideoStream(usePiCamera=self.usePiCamera).start()

        # Allow camera or video file to warm up
        print("Warming up camera or video file")
        time.sleep(2.0)

        # Record to video output file
        if self.outputFile:
            print("Record to file:", self.outputFile)
            mvWidth = 1208
            mvHeight = 756
            fourcc = cv2.VideoWriter_fourcc('M','J','P','G')
            self.writer = cv2.VideoWriter(self.outputFile, fourcc, 30, (mvWidth, mvHeight), True)

        return self


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


    # Write output frame
    def write(output):
        if self.writer is not None:
            self.writer.write(output)


    # Stop stream
    def stop(self):
        # Stop video/camera stream
        if self.videoFile is not None:
            self.stream.stop()
        else:
            self.stream.release()

        # Stop recording video file
        if outputFile:
            self.writer.release()
