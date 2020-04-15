#########################
# Automated Foosball    #
#########################

# USAGE
# python main.py
# python main.py --debug
# python main.py --video input.mp4
# python main.py --video input.mp4 --output output.mp4

# import the necessary packages
import argparse
import cv2
import datetime
import time
from foosball import foosball
from video import videoStream


# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-d", "--debug", help="whether or not to show debug mode", action="store_true")
ap.add_argument("-v", "--video", help="path to the (optional) video file")
ap.add_argument("-o", "--output", help="path to output video file")
args = vars(ap.parse_args())

# Define HSV bounds for foosball
ballMin1HSV = (0, 20, 20)
ballMax1HSV = (10, 255, 255)
ballMin2HSV = (170, 20, 20)
ballMax2HSV = (180, 255, 255)

# Initialize camera / video and allow time for camera to warm up
if args["video"]:
	vs = cv2.VideoCapture(args["video"])
else:
	vs = videoStream().start()
	time.sleep(2.0)

# Initialize foosball game
fb = foosball(args["debug"]).start()

# Record video output to file
writer = None
if args["output"]:
	#height = (360 * 2) + (20 * 3) + (8 * 2)
	#width = 640 * 2 + 8
	fourcc = cv2.VideoWriter_fourcc('M','J','P','G')
	writer = cv2.VideoWriter(self.outputFile, fourcc, 30, (1288, 796), True)

# Start FPS timer
startTime = datetime.datetime.now()
numFrames = 0

# Main loop
while fb.gameIsActive:
	print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"), "Start main loop")
	print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"), "Read frame begin")

	# Read next frame
	if args["video"]:
		ret, frame = vs.read()
		if ret == True:
			fb.rawFrame = frame
			print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"), "Read VIDEO frame end")
			print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"), "Resize VIDEO frame begin")
			fb.frame = cv2.resize(frame, (640, 480), interpolation=cv2.INTER_AREA)
			print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"), "Resize VIDEO frame end")
		else:
			if args["debug"]:
				print("No frame exists, reached EOF")
			break

	# Live camera stream
	else:
		fb.rawFrame = vs.read()
		print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"), "Read CAMERA frame end")
	    # Use ArUco markers to identify table boundaries and crop image
		print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"), "Detect CAMERA table begin")
		fb.detectTable()
		print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"), "Detect CAMERA table end")

	# Update FPS counter
	numFrames += 1

	# Detect position of the foosball and the players
	#fb.detectPlayers()
	ballPosition = fb.detectFoosball(ballMin1HSV, ballMax1HSV, ballMin2HSV, ballMax2HSV)

	# Keep processing if foosball was not detected
	# This usually means a goal was scored
	# If the ball is occluded, we still track the current (projected) location along with a timeout counter
	if ballPosition is not None:
		if args["debug"]:
			print("Foosball position was detected!")

		# At this point, the foosball potiion is known
		# Determine the tracking method to use
		fb.determineTrackingMethod()

		# Calculate the target position of the foosmen rows based on the tracking method

		# Apply takeover to determine in each row should track the ball
		#fb.foosmenTakeover()

		# Calculate the motor positions required to put the tracking foosmen in the desired location
		# Determine the amount of movement needed for each of the linear and rotational motors to move to desired position
		# Move the motors based on the desired position
		#fb.determineMotorMovement()
		#fb.moveMotors()


		# Check for goal and update score
		#fb.checkForGoal()

	# Video processing
	# Build multi view display and show on screen
	fb.updateDisplay([fb.frame, fb.mask3, fb.contoursImg, fb.finalImg])

	# Write frame to output file
	if writer is not None:
		writer.write(fb.output)

	# Calculate number of seconds that have elapsed and display FPS
	ts = (datetime.datetime.now() - startTime).total_seconds()
	print("[INFO] Avg FPS: {:.2f}".format(numFrames / ts))

	# Handle user input
	# Stop the loop if the "q" key is pressed
	if cv2.waitKey(1) & 0xFF == ord("q"):
		break


# Stop timer and display FPS information
ts = (datetime.datetime.now() - startTime).total_seconds()
print("[INFO] elasped time: {:.2f}".format(ts))
print("[INFO] Avg FPS: {:.2f}".format(numFrames / ts))

# Stop recording video file
if writer is not None:
	writer.release()

# Stop video/camera feed and output writer
if args["video"]:
	vs.release()
else:
	vs.stop()

# Close all windows
cv2.destroyAllWindows()
