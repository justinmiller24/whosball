#########################
# Automated Foosball    #
#########################

# USAGE
# python main.py
# python main.py --debug
# python main.py --output output.mp4

# import the necessary packages
import argparse
import cv2
import time
from foosball import foosball
from video import videoStream

print("Start Main Script")


# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("--debug", help="whether or not to show debug mode", action="store_true")
ap.add_argument("--output", help="path to output video file")
args = vars(ap.parse_args())

# Initialize camera and allow time to warm up
vs = videoStream().start()
time.sleep(2.0)

# Initialize foosball game
fb = foosball(args["debug"]).start()

# Record video output to file
writer = None
if args["output"]:
	h = fb.dim["yPixels"] * 2 + (20 * 3) + (8 * 2)
	w = fb.dim["xPixels"] * 2 + 8
	fourcc = cv2.VideoWriter_fourcc('M','J','P','G')
	writer = cv2.VideoWriter(args["output"], fourcc, 30, (w, h), True)

print("Pause Before Main Loop Begins...")
time.sleep(2.0)

# Main loop
while fb.gameIsActive:
	print()
	fb.log("Main loop begin")

	# Read frame from camera stream and update FPS counter
	rawFrame = vs.read()
	fb.readFrame(rawFrame)

	# Use ArUco markers to identify table boundaries and crop image
	fb.detectTable()

	# Detect players and foosball
	fb.detectPlayers()
	fb.detectFoosball()

	# Keep processing if foosball was not detected
	# This usually means a goal was scored
	# If the ball is occluded, we still track the current (projected) location along with a timeout counter
	if fb.foosballPosition is not None:

		# At this point, the foosball potiion is known
		# Determine the tracking method to use
		fb.determineTrackingMethod()

		# Calculate the target position of the foosmen rows based on the tracking method

		# Apply takeover to determine in each row should track the ball
		#fb.foosmenTakeover()

		# Calculate the motor positions required to put the tracking foosmen in the desired location
		# Determine the amount of movement needed for each of the linear and rotational motors to move to desired position
		# Move the motors based on the desired position
		fb.determineMotorMovement()
		fb.moveMotors()


		# Check for goal and update score
		#fb.checkForGoal()

	# Video processing
	# Build multi view display, show on screen, and handle user input
	# Stop loop if the "q" key is pressed
	fb.log("Update display begin")
	fb.updateDisplay([fb.frame, fb.mask3, fb.contoursImg, fb.finalImg])
	if cv2.waitKey(1) & 0xFF == ord("q"):
		break
	fb.log("Update display end")

	# Write frame to output file
	if writer is not None:
		writer.write(fb.output)

	fb.log("Main loop end")


# Stop timer and display FPS information
print()
print("[INFO] Elasped time: {:.2f}".format(fb.elapsedTime))
print("[INFO] Avg FPS: {:.2f}".format(fb.numFrames / fb.elapsedTime))
print("[INFO] Avg FPS: {:.2f}".format(fb.fps))

# Do a bit of cleanup
# Stop camera, video file, and destroy all windows
cv2.destroyAllWindows()
if writer is not None:
	writer.release()
vs.stop()
