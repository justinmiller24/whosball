from imutils.video import VideoStream
import cv2
import display
import imutils
import time


class videoStream:

    # Initialize video stream instance
    def __init__(self, debug=False, usePiCamera=False, videoFile=None, outputFile=None):

        self.debug = debug
        self.usePiCamera = usePiCamera
        self.videoFile = videoFile
        self.outputFile = outputFile
        self.writer = None

        if self.debug:
            display.out("Initialize Camera")


    # Start stream
    def start(self):

        if self.videoFile is not None:
            self.stream = cv2.VideoCapture(self.videoFile)
        else:
            self.stream = VideoStream(usePiCamera=self.usePiCamera).start()

        # Allow camera or video file to warm up
        if self.debug:
            display.out("Warming up camera or video file")
        time.sleep(2.0)

        # Record to video output file
        if self.outputFile:
            if self.debug:
                display.out("Record to file:", self.outputFile)
            mvWidth = 1208
            mvHeight = 756
            fourcc = cv2.VideoWriter_fourcc('M','J','P','G')
            self.writer = cv2.VideoWriter(self.outputFile, fourcc, 30, (mvWidth, mvHeight), True)

        return self


    # Get next frame from camera or video stream and resize
    def getNextFrame(self):
        if self.debug:
            display.out("Get Next Frame")
        self.frame = self.stream.read()
        #self.frame = self.frame[1] if args.get("video", False) else self.frame
        self.frame = self.frame[1] if self.videoFile is not None else self.frame

        if self.frame is not None:
            self.frame = imutils.resize(self.frame, width=600)

        return self.frame


    def getHSVImage(self):
        if self.debug:
            display.out("Get HSV image")
        self.blurred = cv2.GaussianBlur(self.frame, (11, 11), 0)
        self.hsv = cv2.cvtColor(self.blurred, cv2.COLOR_BGR2HSV)
        return self.hsv


    def getGrayscale(self):
        if self.debug:
            display.out("Get grayscale image")
        self.gray = cv2.cvtColor(self.frame, cv2.COLOR_RGB2GRAY)
        return self.gray
        #self.grayscale = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        #return self.grayscale


    # Write output frame
    def write(self, output):
        if self.writer is not None:
            self.writer.write(output)


    # Stop stream
    def stop(self):
        # Stop video/camera stream
        if self.videoFile is not None:
            self.stream.release()
        else:
            self.stream.stop()

        # Stop recording video file
        if self.outputFile:
            self.writer.release()
