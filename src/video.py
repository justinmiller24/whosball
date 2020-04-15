# import the necessary packages
from picamera.array import PiRGBArray
from picamera import PiCamera
from threading import Thread


class videoStream:

    # Initialize
    #def __init__(self, debug=False, resolution=(640, 480), framerate=32, videoFile=None, outputFile=None):
    def __init__(self, debug=False, resolution=(640, 480), framerate=32):

        self.debug = debug
        #self.videoFile = videoFile
        #self.outputFile = outputFile
        #self.writer = None

        #if self.videoFile is not None:
            #self.stream = cv2.VideoCapture(self.videoFile)
        #else:
            #self.stream = VideoStream(usePiCamera=self.usePiCamera).start()

        # initialize the camera and stream
        self.camera = PiCamera()
        self.camera.resolution = resolution
        self.camera.framerate = framerate
        self.rawCapture = PiRGBArray(self.camera, size=resolution)
        self.stream = self.camera.capture_continuous(self.rawCapture, format="bgr", use_video_port=True)

        # Record to video output file
        #if self.outputFile:
            #padding = 8
            #mvHeight = (360 * 2) + (20 * 3) + (padding * 2)
            #mvWidth = 640 * 2 + padding
            #fourcc = cv2.VideoWriter_fourcc('M','J','P','G')
            #self.writer = cv2.VideoWriter(self.outputFile, fourcc, 30, (mvWidth, mvHeight), True)

        # initialize the frame and the variable used to indicate
        # if the thread should be stopped
        self.frame = None
        self.stopped = False


    # Start stream
    def start(self):
        # start the thread to read frames from the video stream
        Thread(target=self.update, args=()).start()
        return self


    def update(self):
        # keep looping infinitely until the thread is stopped
        for f in self.stream:
            # grab the frame from the stream and clear the stream in
            # preparation for the next frame
            self.frame = f.array
            self.rawCapture.truncate(0)

            # if the thread indicator variable is set, stop the thread
            # and resource camera resources
            if self.stopped:
                self.stream.close()
                self.rawCapture.close()
                self.camera.close()
                # Stop video/camera stream
                #if self.videoFile is not None:
                    #self.stream.release()
                #else:
                    #self.stream.stop()

            # Stop recording video file
            #if self.outputFile:
                #self.writer.release()
            return


    # Return the frame most recently used
    def read(self):
        #self.frame = self.stream.read()
        #self.frame = self.frame[1] if self.videoFile is not None else self.frame
        #if self.frame is not None:
            #self.frame = imutils.resize(self.frame, width=600)
        return self.frame


    def stop(self):
        # indicate that the thread should be stopped
        self.stopped = True


        # Write output frame
        #def write(self, output):
        #if self.writer is not None:
            #self.writer.write(output)
