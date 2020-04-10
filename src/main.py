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
from video import videoStream
from foosball import foosball


# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-d", "--debug", help="whether or not to show debug mode", action="store_true")
ap.add_argument("-s", "--display", type=int, default=1, help="whether or not to display output")
ap.add_argument("-p", "--picamera", help="whether or not the Raspberry Pi camera should be used", action="store_true")
ap.add_argument("-v", "--video", help="path to the (optional) video file")
ap.add_argument("-o", "--output", help="path to output video file")
args = vars(ap.parse_args())

# Define HSV bounds for foosball
ballMin1HSV = (0, 20, 20)
ballMax1HSV = (10, 255, 255)
ballMin2HSV = (170, 20, 20)
ballMax2HSV = (180, 255, 255)

# Define coordinates for foosball table in top-left, top-right, bottom-left, and bottom-right order
tL = (73,130)
tR = (557,136)
bL = (59,405)
bR = (561,414)
origCoords = [tL, tR, bL, bR]

# Initialize camera / video and foosball game
v = videoStream(args["debug"], args["picamera"], args["video"], args["output"]).start()
f = foosball(args["debug"], args["display"]).start()

# Main loop
while f.gameIsActive:

	# Read next frame. If no frame exists, then we've reached the end of the video.
	frame = v.getNextFrame()
	if frame is None:
		if args["debug"]:
			print("No frame exists, reached end of file")
		break

	# Save current frame
	f.setRawFrame(frame)

	# Transform perspective based on key points
	origImg = f.transformImagePerspective(origCoords)

	# Detect position of the foosball and the players
	#f.detectPlayers()
	ballPosition = f.detectFoosball()

	# Keep processing if foosball was not detected
	# This usually means a goal was scored
	# If the ball is occluded, we still track the current (projected) location along with a timeout counter
	if ballPosition is None:
		if args["debug"]:
			print("Foosball position was not detected")
		continue

	# At this point, the foosball potiion is known
	# Determine the tracking method to use
	f.determineTrackingMethod()

	# Calculate the target position of the foosmen rows based on the tracking method

	# Apply takeover to determine in each row should track the ball
	#f.foosmenTakeover()

	# Calculate the motor positions required to put the tracking foosmen in the desired location
	# Determine the amount of movement needed for each of the linear and rotational motors to move to desired position
	# Move the motors based on the desired position
	#f.determineMotorMovement()
	#f.moveMotors()


	# Check for goal and update score
	#f.checkForGoal()

	# Video processing
	if (args["display"] or args["output"]):

		# Build multi view display and show on screen
		f.updateDisplay(f.frame, f.mask3, f.contoursImg, f.finalImg)

		# Write display to video output file
		if args["output"]:
			v.write(f.output)

		# Show display on screen
		if args["display"]:
			cv2.imshow("Output", f.output)

			# Display original (uncropped) image
			# Show transformation coordinates on original image
			for (x, y) in tableCoords:
				cv2.circle(frame, (x, y), 5, (0, 255, 0), -1)
			cv2.namedWindow("Raw")
			cv2.moveWindow("Raw", 1250, 100)
			cv2.imshow("Raw", frame)

		# Handle user input
		# Stop the loop if the "q" key is pressed
		if cv2.waitKey(1) & 0xFF == ord("q"):
			break


# Stop video/camera feed and output writer
v.stop()

# close all windows
cv2.destroyAllWindows()
