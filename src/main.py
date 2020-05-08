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
from foosball import Foosball
from foosmen import Foosmen
from video import videoStream

print("Starting Main Script")


# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("--debug", help="whether or not to show debug mode", action="store_true")
ap.add_argument("--output", help="path to output video file")
args = vars(ap.parse_args())


##########################################################################
# This section initializes the camera, foosball table, and motors        #
##########################################################################

# Initialize camera and allow time to warm up
print("Initialize camera")
vs = videoStream().start()
time.sleep(2.0)

# Initialize foosball game
print("Initialize game")
fb = Foosball(args["debug"]).start()

# Initialize players and motors
print("Initialize players and motors")
# Goalie
# The 1st row has 3 men, spaced 7 1/8" apart, and 8 1/2" of linear movement
f0 = Foosmen(0, 3, fb.vars["row0"][0], fb.vars["row0"][1], fb.vars["foosmenWidth"]).start()
# Defense
# The 2nd row has 2 men, spaced 9 5/8" apart, and 13 3/8" of linear movement
f1 = Foosmen(1, 2, fb.vars["row1"][0], fb.vars["row1"][1], fb.vars["foosmenWidth"]).start()
# Midfield
# The 3rd row has 5 men, spaced 5" apart, and 4 1/4" of linear movement
f3 = Foosmen(3, 5, fb.vars["row2"][0], fb.vars["row2"][1], fb.vars["foosmenWidth"]).start()
# Offense
# The 4th row has 3 men, spaced 7 1/8" apart, and 8 1/2" of linear movement
f5 = Foosmen(5, 3, fb.vars["row3"][0], fb.vars["row3"][1], fb.vars["foosmenWidth"]).start()

# Record video output to file
writer = None
if args["output"]:
	print("Initialize video output")
	fourcc = cv2.VideoWriter_fourcc('M','J','P','G')
	writer = cv2.VideoWriter(args["output"], fourcc, 30, (fb.vars["width"], fb.vars["height"] + 120), True)


# Main loop
while fb.gameIsActive:
	print()
	fb.log("[INFO] Main loop begin")


	##########################################################################
	# This section grabs the latest image from the camera stream             #
	# and detects the table, players, and ball                               #
	##########################################################################

	# Read frame from camera stream and update FPS counter
	rawFrame = vs.read()
	fb.readFrame(rawFrame)

	# Because the camera or table can move during play, we place ArUco markers
	# in each corner of the foosball table and then detect them in real time.
	# This allows us to effectively place "boundary points" in each corner and
	# then crop our live stream to these specific points.
	fb.findTable()

	# Find location of the players
	fb.findPlayers("RED")
	fb.findPlayers("BLUE")

	# Find location of the foosball
	fb.findBall()

	# Only continue if the location of the foosball is known
	if fb.isKnownBallPosition():


		##########################################################################
		# This section determines which row is in control of the ball,           #
		# calculates the position(s) required for each row,                      #
		# detemines the movement(s) needed for each row,                         #
		# and sends a signal to move the motor(s) based on the movement needed.  #
		##########################################################################

		# Calculate the most likely position of the ball in the next frame
		projectedX = fb.getProjectedX()

		# Find out which foosmen row is most likely to control the ball next
		closestRow = fb.getClosestRow(projectedX)

		# Goalie
		if closestRow == 0 and projectedX >= fb.vars["foosmenRED"][0]:
			fb.log("[INFO] Goal row is in control of the ball")
			fb.log("[MOTOR] Goal row KICK!")
			f0.rotateTo(75)

		# Defense
		elif closestRow == 1 and projectedX >= fb.vars["foosmenRED"][1]:
			fb.log("[INFO] Defense row is in control of the ball")
			fb.log("[MOTOR] Defense row KICK!")
			f1.rotateTo(75)

		# Midfield
		elif closestRow == 3 and projectedX >= fb.vars["foosmenRED"][2]:
			fb.log("[INFO] Midfield row is in control of the ball")
			fb.log("[MOTOR] Midfield row KICK!")
			f3.rotateTo(75)

		# Offense
		elif closestRow == 5 and projectedX >= fb.vars["foosmenRED"][3]:
			fb.log("[INFO] Offense row is in control of the ball")
			fb.log("[MOTOR] Offense row KICK!")
			f5.rotateTo(75)


	##########################################################################
	# This section displays output on the screen and records video output    #
	##########################################################################

	# Display original (uncropped) image and transformation coordinates
	origImg = fb.rawFrame.copy()
	if fb.origCoords is not None:
		for (x, y) in fb.origCoords:
			cv2.circle(origImg, (x, y), 5, (0, 255, 0), -1)
	cv2.namedWindow("Raw")
	cv2.moveWindow("Raw", 1250, 100)
	cv2.imshow("Raw", origImg)


	# Build output frame, show on screen, and handle user input
	# Stop loop if the "q" key is pressed
	out = fb.buildOutputFrame()
	cv2.imshow("Output", out)
	if cv2.waitKey(1) & 0xFF == ord("q"):
		break

	# Write frame to output file
	if writer is not None:
		writer.write(out)


# Stop timer and display FPS information
print()
print("Ending Main Script")
print("Elasped time: {:.2f}".format(fb.elapsedTime))
print("Avg FPS: {:.2f}".format(fb.fps))
print()


# Do a bit of cleanup
# Stop camera, video file, and destroy all windows
cv2.destroyAllWindows()
if writer is not None:
	writer.release()
vs.stop()
