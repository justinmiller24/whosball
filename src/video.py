from imutils.video import VideoStream
import cv2
import datetime
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
            self.log("Initialize Camera")


    # Start stream
    def start(self):

        if self.videoFile is not None:
            self.stream = cv2.VideoCapture(self.videoFile)
        else:
            self.stream = VideoStream(usePiCamera=self.usePiCamera).start()

        # Allow camera or video file to warm up
        if self.debug:
            self.log("Warming up camera or video file")
        time.sleep(2.0)

        # Record to video output file
        if self.outputFile:
            if self.debug:
                self.log("Record to file:", self.outputFile)
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
            self.log("Get Next Frame")
        self.frame = self.stream.read()
        self.frame = self.frame[1] if self.videoFile is not None else self.frame

        #if self.frame is not None:
            #self.frame = imutils.resize(self.frame, width=600)

        return self.frame


    # Write output frame
    def write(self, output):
        if self.debug:
            self.log("Write output frame function")

        if self.writer is not None:
            self.writer.write(output)


    # Stop stream
    def stop(self):
        if self.debug:
            self.log("Stop or release video stream")

        # Stop video/camera stream
        if self.videoFile is not None:
            self.stream.release()
        else:
            self.stream.stop()

        # Stop recording video file
        if self.outputFile:
            self.writer.release()

    def log(self, msg):
        print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"), msg)
