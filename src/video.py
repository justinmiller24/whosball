from imutils.video import VideoStream
from imutils import perspective
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
            #mvWidth = 1208
            #mvHeight = 756
            padding = 8
            mvHeight = (297 * 2) + (20 * 3) + (8 * 2)
            mvWidth = 510 * 2 + 8
            #mvWidth = 1028
            #mvHeight =
            #mvHeight = (h * 2) + (20 * 3) + (padding * 2)
            fourcc = cv2.VideoWriter_fourcc('M','J','P','G')
            self.writer = cv2.VideoWriter(self.outputFile, fourcc, 30, (mvWidth, mvHeight), True)

        return self


    # Get next frame from camera or video stream and resize
    def getNextFrame(self):
        if self.debug:
            display.out("Get Next Frame")
        self.frame = self.stream.read()
        self.frame = self.frame[1] if self.videoFile is not None else self.frame

        #if self.frame is not None:
            #self.frame = imutils.resize(self.frame, width=600)

        return self.frame


    # Transform perspective based on 4 input points (coords)
    def perspectiveTransform(self, coords):
        origImg = self.frame.copy()

        # Grab image dimensions and determine center point
        (h, w) = origImg.shape[:2]
        #(cX, cY) = (w // 2, h // 2)

        # loop over the points and draw them on the cloned image
        #for (x, y) in pts:
            #cv2.circle(clone, (x, y), 5, (0, 255, 0), -1)

        # Perspective transform
        # apply the four point tranform to obtain a "birds eye view" of image
        self.frame = perspective.four_point_transform(origImg, coords)

        # Resulting frame should be 510px x 297px
        return self.frame


    # Rotate and crop
    def rotateAndCrop(self):

        # grab the rotation matrix (apply the negative of the angle to rotate clockwise)
        M = cv2.getRotationMatrix2D((cX, cY), 1, 1.0)
        # Rotate and crop image
        rotatedImg = cv2.warpAffine(image, M, (w, h))
        croppedImg = rotatedImg[125:h-62, 50:w-65]
        croppedImg = rotatedImg[100:h - 50, 25: w - 25]

        self.frame = croppedImg

        return self.frame


    # Set next frame based on cropped image
    #def setNextFrame(self, image):
        #if self.debug:
            #display.out("Set Next Frame")
        #self.frame = image

        #return self.frame


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
