#########################
# Automated Foosball    #
#########################

# USAGE
# python main.py
# python main.py --debug
# python main.py --picamera
# python main.py --video input-video.mp4
# python main.py --video input-video.mp4 --output output-video.mp4

# import the necessary packages
import argparse
import cv2
import time
from imutils.video import FPS
from foosball import foosball
from video import videoStream


# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-d", "--debug", help="whether or not to show debug mode", action="store_true")
#ap.add_argument("-s", "--display", type=int, default=1, help="whether or not to display output")
ap.add_argument("-p", "--picamera", help="whether or not the Raspberry Pi camera should be used", action="store_true")
ap.add_argument("-v", "--video", help="path to the (optional) video file")
ap.add_argument("-o", "--output", help="path to output video file")
args = vars(ap.parse_args())

# Define HSV bounds for foosball
ballMin1HSV = (0, 20, 20)
ballMax1HSV = (10, 255, 255)
ballMin2HSV = (170, 20, 20)
ballMax2HSV = (180, 255, 255)

# Initialize camera / video and foosball game
#vs = videoStream(args["debug"], args["picamera"], args["video"], args["output"]).start()
vs = videoStream().start()
time.sleep(2.0)
fps = FPS().start()
fb = foosball(args["debug"]).start()

# Main loop
while fb.gameIsActive:

	# Read next frame
	fb.rawFrame = vs.read()

	# Update FPS counter
	fps.update()

	#if fb.rawFrame is None:
		#if args["debug"]:
			#print("No frame exists, reached end of file")
		#break

    # Use ArUco markers to identify table boundaries and crop image
	fb.detectTable()

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

	# Write display to video output file
	if args["output"]:
		vs.write(fb.output)

	# Handle user input
	# Stop the loop if the "q" key is pressed
	if cv2.waitKey(1) & 0xFF == ord("q"):
		break


# Stop the timer and display FPS information
fps.stop()
print("[INFO] elasped time: {:.2f}".format(fps.elapsed()))
print("[INFO] approx. FPS: {:.2f}".format(fps.fps()))

# Stop video/camera feed and output writer
vs.stop()

# Close all windows
cv2.destroyAllWindows()
