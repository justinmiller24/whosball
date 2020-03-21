from imutils.video import VideoStream
import time


def start(outputFile=None):

    # if a video path was not supplied, grab the reference to the webcam
    # otherwise, grab a reference to the video file
    if not args.get("video", False):
    	#vs = VideoStream(src=0).start()
    	vs = VideoStream(usePiCamera=args["picamera"] > 0).start()
    else:
    	vs = cv2.VideoCapture(args["video"])


    # allow the camera or video file to warm up
    print("Warming up camera or video file")
    time.sleep(2.0)


    # Define the codec and create VideoWriter object
    if outputFile is not None:
    	print("Recording to file:", outputFile)
    	fourcc = cv2.VideoWriter_fourcc('M','J','P','G')
    	writer = None


def stop(outputFile=None):
    # if we are not using a video file, stop the camera video stream
    if not args.get("video", False):
    	vs.stop()

    # otherwise, release the camera
    else:
    	vs.release()

    # Stop recording video file
    if outputFile:
    	writer.release()
