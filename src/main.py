#########################
# Automated Foosball    #
#########################

# USAGE
# python main.py
# python main.py --picamera 1
# python main.py --video test-video.mp4
# python main.py --video input-video.mp4 --output output-video.mp4

# import the necessary packages
from __future__ import print_function
from collections import deque
import argparse
import cv2
#import datetime
# Local Files
import detection
import gui
import motors
import video

# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-d", "--display", type=int, default=-1, help="Whether or not frames should be displayed")
ap.add_argument("-p", "--picamera", type=int, default=-1, help="whether or not the Raspberry Pi camera should be used")
ap.add_argument("-v", "--video", help="path to the (optional) video file")
ap.add_argument("-o", "--output", help="path to output video file")
args = vars(ap.parse_args())

outputFile = args["output"] if if args.get("output", False) else None

# Define Table Size
#table_dim_cm = (56 * 2.54, 29 * 2.54)


# Initialize
detection.init()
video.start(outputFile)

# Main loop
gameInProgress = True
while gameInProgress:
	detection.getFrame(useVideoStream = args.get("video", False))
	detection.detectBall(outputFile)
	detection.detectPlayers()
	detection.detectScore()

	motors.determineMove()
	motors.move()

	# Update display
	if args["display"] > 0:
		gui.updateDisplay()

	# Handle user input
	# Pause if the 'p' key is pressed
	# Exit if the 'q' key is pressed
	key = gui.userInput()
	if key == ord("p"):
		gameInProgress = False
	if key == ord("q"):
		break

video.stop(outputFile)

# close all windows
cv2.destroyAllWindows()
