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
import math
import time
from camera import videoStream
from foosball import Foosball
from players import Foosmen

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
# The goalie (0) row has 3 men, spaced 7 1/8" apart, and 8 1/2" of linear movement
# The defense (1) row has 2 men, spaced 9 5/8" apart, and 13 3/8" of linear movement
# The midfield (3) row has 5 men, spaced 5" apart, and 4 1/4" of linear movement
# The offense (5) row has 3 men, spaced 7 1/8" apart, and 8 1/2" of linear movement
print("Initialize players and motors")
row0 = Foosmen(0, 3, None, None, fb.vars["row0"][0], fb.vars["row0"][1], fb.vars["foosmenWidth"]).start()
row1 = Foosmen(1, 2, None, None, fb.vars["row1"][0], fb.vars["row1"][1], fb.vars["foosmenWidth"]).start()
row3 = Foosmen(3, 5, (17, 27), (23, 24), fb.vars["row2"][0], fb.vars["row2"][1], fb.vars["foosmenWidth"]).start()
row5 = Foosmen(5, 3, None, None, fb.vars["row3"][0], fb.vars["row3"][1], fb.vars["foosmenWidth"]).start()
players = [row0, row1, None, row3, None, row5, None, None]

# Timer for number of frames in holding pattern
idleFrames = 0


# Record video output to file
writer = None
if args["output"]:
	print("Initialize video output")
	fourcc = cv2.VideoWriter_fourcc('M','J','P','G')
	writer = cv2.VideoWriter(args["output"], fourcc, 30, (fb.vars["outputWidth"], fb.vars["outputHeight"]), True)


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

	# Find goal and display overlay
	fb.findGoal()

	# Find location of the foosball
	fb.findBall()

	# Find location of the players
	fb.findPlayers("RED")
	fb.findPlayers("BLUE", True)


	##########################################################################
	# Display to screen and record video output                              #
	##########################################################################

	# Display original (uncropped) image and transformation coordinates
	origImg = fb.rawFrame.copy()
	if fb.tableCoords is not None:
		#origCoords = np.array(fb.tableCoords, dtype="float32")
		#for (x, y) in origCoords:
		for (x, y) in fb.tableCoords:
			cv2.circle(origImg, (int(x), int(y)), 5, (0, 255, 0), -1)
	cv2.namedWindow("Raw")
	cv2.moveWindow("Raw", 1250, 100)
	cv2.imshow("Raw", origImg)

	# Build output frame
	out = fb.buildOutputFrame()

	# Show on screen
	cv2.imshow("Output", out)

	# Write frame to output file
	if writer is not None:
		writer.write(out)

	# Handle user input. Stop loop if the "q" key is pressed.
	if cv2.waitKey(1) & 0xFF == ord("q"):
		break

	# Only continue if the location of the foosball is known
	if fb.foosballPosition is None:
		continue


	##########################################################################
	# Determine how to respond based on current conditions                   #
	##########################################################################

	# Determine closest row to ball and closest row to future position of ball (next 3 frames)
	currentPosition = fb.ballPositions[-1:][0]
	closestRow = fb.getClosestRow(currentPosition[0])
	fb.getControllingRow()
	projectedRow = fb.getClosestRow(currentPosition[0] + 3 * fb.deltaX)


	# Check if ball is coming towards us and will change possession within next 3 frames
	if projectedRow < closestRow:

		# Reset counter
		idleFrames = 0

		# Loop through each row.
		for row in [0, 1, 3, 5]:

			# For rows in between ball and goal, calculate direct or indirect interception point.
			if row < closestRow:

				# Determine intersecting y-coordinate based on x-coordinate
				projectedY = fb.getIntersectingYPos(fb.vars["rowPosition"][row])

				# If row can intercept, move to intercept. Otherwise, do not move.

				#TODO: update these variables
				currentYForRow = 0
				maxYSpeedOfRow = 1

				numFramesUntilRow = (fb.vars["rowPosition"][row] - currentPosition[0]) // fb.deltaX
				yDistanceNeededToMove = abs(currentPosition[1] - projectedY)
				numFramesNeededToMove = yDistanceNeededToMove // maxYSpeedOfRow
				if numFramesNeededToMove < numFramesUntilRow:
					fb.log("[INFO] Row{} move to intercept at {}".format(row, projectedY))
					players[row].moveTo(projectedY)
				else:
					fb.log("[INFO] Row{} not able to intercept at {}, do nothing".format(row, projectedY))

			# For rows not in between ball and goal, move to default defensive position.
			else:
				fb.log("[INFO] Row{} not in between ball and goal, move to default position".format(row))
				players[row].defaultPosition()


	# Opponent is in control of ball and the ball is not moving towards our goal
	elif fb.controllingRow in [2, 4, 6, 7]:

		# Reset counter
		idleFrames = 0

		# Move all rows to default defensive position
		for row in [0, 1, 3, 5]:
			players[row].defaultPosition()


	# TODO: build out based on scenario
	# For now, we basically just calculate the angle between current position and the opponent's goal, and shoot
	# We are in control of ball and there is a direct or indirect opening between ball and opponent goal
	# We are in control of ball, no path exists, and our offense is in control of ball
	# We are in control of ball, no path exists, and our midfield is in control of ball
	# We are in control of ball, no path exists, and our defense is in control of ball
	# We are in control of ball, no path exists, and our goalie is in control of ball
	elif fb.controllingRow in [0, 1, 3, 5]:

		# Reset counter
		idleFrames = 0

		# Make sure ball will be ahead of players on next frame
		if fb.projectedPosition[0] >= fb.vars["rowPosition"][fb.controllingRow]:

			# Calculate optimal angle between ball and opponent's goal
			tempX = fb.vars["width"] - fb.ballPositions[-1:][0][0]
			tempY = fb.vars["height"] / 2 - fb.ballPositions[-1:][0][1]

			# Calculate arc tangent (in radians) and convert to degrees
			angle = math.atan2(tempX, tempY) / math.pi * 180

			fb.log("[INFO] Row{} kick towards opponent goal at angle {}".format(fb.controllingRow, angle))
			players[fb.controllingRow].kickAngle(angle, tempX, tempY)

		else:
			fb.log("[INFO] Row{} pause, since ball will not be ahead of row on next frame".format(fb.controllingRow))


	# Neither player is in control of the ball
	elif fb.controllingRow is -1:

		# Increment counter
		idleFrames = idleFrames + 1

		# If the number of idle frames exceeds threshold, pause game and show warning/error message
		if idleFrames > 100:
			fb.log("[INFO] Number of idle frames exceeds threshold, end game")
			fb.gameIsActive = False


	# Something went wrong
	else:
		fb.log("[INFO] Controlling row: {}".format(fb.controllingRow))
		fb.log("[INFO] Something went wrong... exiting now")
		fb.gameIsActive = False


# Stop timer and display FPS information
print()
print("Ending Main Script")
print("Elasped time: {:.2f}".format(fb.elapsedTime))
print("Avg FPS: {:.2f}".format(fb.fps))
print()

# Release motors
for row in [0, 1, 3, 5]:
	players[row].releaseMotors()


# Do a bit of cleanup
# Stop camera, video file, and destroy all windows
cv2.destroyAllWindows()
if writer is not None:
	writer.release()
vs.stop()
