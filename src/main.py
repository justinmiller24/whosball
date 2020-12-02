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
from foosmen import Foosmen

print("Starting Main Script")


# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("--debug", help="whether or not to show debug mode", action="store_true")
ap.add_argument("--nopreview", help="whether or not to hide video preview", action="store_true")
ap.add_argument("--raw", help="whether or not to show raw video capture", action="store_true")
ap.add_argument("--output", help="path to output video file")
args = vars(ap.parse_args())

# Show preview
showPreview = not args["nopreview"]


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

# The goalie row (0) has 3 men, located at xPos 29, spaced 7 1/8" apart, and 8 1/2" of linear movement
row0 = Foosmen(0, 3, 29, 97.54, 116.37, None, None).start()

# The defense row (1) has 2 men, located at xPos 114, spaced 9 5/8" apart, and 13 3/8" of linear movement
row1 = Foosmen(1, 2, 114, 131.77, 183.11, None, None).start()

# The midfield row (3) has 5 men, located at xPos 280, spaced 5" apart, and 4 1/4" of linear movement
row3 = Foosmen(3, 5, 280, 68.45, 58.18, None, (17, 27, 22)).start()

# The offense row (5) has 3 men, located at xPos 443, spaced 7 1/8" apart, and 8 1/2" of linear movement
row5 = Foosmen(5, 3, 443, 97.54, 116.37, None, None).start()

players = [row0, row1, None, row3, None, row5, None, None]


# # Calculate the lower and upper bounds for each foosmen
# 'foosmen': np.array([
#     # Goalie
#     (17, 148),                          # Min/max coordinates (in pixels)
#     (115, 246),                         # Min/max coordinates (in pixels)
#     (212, 343),                         # Min/max coordinates (in pixels)
#     # Defense
#     (17, 211),                          # Min/max coordinates (in pixels)
#     (149, 343),                         # Min/max coordinates (in pixels)
#     # Midfield
#     (17, 69),                           # Min/max coordinates (in pixels)
#     (85, 137),                          # Min/max coordinates (in pixels)
#     (154, 206),                         # Min/max coordinates (in pixels)
#     (222, 274),                         # Min/max coordinates (in pixels)
#     (291, 343),                         # Min/max coordinates (in pixels)
#     # Offense
#     (17, 148),                          # Min/max coordinates (in pixels)
#     (115, 246),                         # Min/max coordinates (in pixels)
#     (212, 343),                         # Min/max coordinates (in pixels)
# ])

# Warm Up Motors
print("Warm up motors")
row3.kick()

# Change direction
#time.sleep(.5)

# Timer for number of frames in holding pattern
idleFrames = 0


# Record video output to file
writer = None
if args["output"]:
	print("Initialize video output: {}".format(args["output"]))
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
	if args["raw"]:
		origImg = fb.rawFrame.copy()
		#if fb.tableCoords is not None:
			#origCoords = np.array(fb.tableCoords, dtype="float32")
			#for (x, y) in origCoords:
			#for (x, y) in fb.tableCoords:
				#cv2.circle(origImg, (int(float(x)), int(float(y))), 5, (0, 255, 0), -1)
		cv2.namedWindow("Raw")
		cv2.moveWindow("Raw", 1250, 100)
		cv2.imshow("Raw", origImg)

	# Build output frame
	out = fb.buildOutputFrame()

	# Show on screen
	if showPreview:
		cv2.imshow("Output", out)

	# Write frame to output file
	if writer is not None:
		writer.write(out)

	# Handle user input. Stop loop if the "q" key is pressed.
	fb.log("[INFO] Wait for user input", True)
	key = cv2.waitKey(1) & 0xFF
	# Quit
	if key == ord("q"):
		break
	# Toggle debug mode
	elif key == ord("d"):
		fb.debug = not fb.debug


	##########################################################################
	# Determine how to respond based on current conditions                   #
	##########################################################################

	# Ensure foosball position is known
	if fb.foosballPosition is None:
		continue

	# Current position of foosball
	currentPosition = fb.ballPositions[-1:][0]

    # Loop through active rows to determine if foosball is within reach
	for row in players:
		if row is not None:

			# Kick if foosball is within reach
			distanceToBall = currentPosition[0] - row.xPos
			if (distanceToBall < 30):
				fb.log("[AI] Foosball current xPos: {}".format(currentPosition[0]))
				fb.log("[AI] Foosmen row {} at xPos {} is within reach of foosball, distance is {}".format(row, row.xPos, distanceToBall))
				fb.log("[AI] KICK!!!")
				players[row].kick()



	# # Determine closest row to ball and closest row to future position of ball (next 3 frames)
	# currentPosition = fb.ballPositions[-1:][0]
	# closestRow = fb.getClosestRow(currentPosition[0])
	# fb.getControllingRow()
	# projectedRow = fb.getClosestRow(currentPosition[0] + 3 * fb.deltaX)
	# fb.log("[INFO] Closest Row: {} Projected Row: {}".format(closestRow, projectedRow))
	#
	#
	#
	# # Check if ball is coming towards us and will change possession within next 3 frames
	# if projectedRow < closestRow:
	#
	# 	# Reset counter
	# 	idleFrames = 0
	#
	# 	# Loop through each row.
	# 	for row in [0, 1, 3, 5]:
	#
	# 		# For rows in between ball and goal, calculate direct or indirect interception point.
	# 		if row < closestRow:
	#
	# 			# Determine intersecting y-coordinate based on x-coordinate
	# 			projectedY = fb.getIntersectingYPos(fb.vars["rowPosition"][row])
	#
	# 			# If row can intercept, move to intercept. Otherwise, do not move.
	#
	# 			#TODO: update these variables
	# 			currentYForRow = 0
	# 			maxYSpeedOfRow = 1
	#
	# 			numFramesUntilRow = (fb.vars["rowPosition"][row] - currentPosition[0]) // fb.deltaX
	# 			yDistanceNeededToMove = abs(currentPosition[1] - projectedY)
	# 			numFramesNeededToMove = yDistanceNeededToMove // maxYSpeedOfRow
	# 			if numFramesNeededToMove < numFramesUntilRow:
	# 				fb.log("[INFO] Row{} move to intercept at {}".format(row, projectedY))
	# 				players[row].moveTo(projectedY)
	# 			else:
	# 				fb.log("[INFO] Row{} not able to intercept at {}, do nothing".format(row, projectedY))
	#
	# 		# For rows not in between ball and goal, move to default defensive position.
	# 		else:
	# 			fb.log("[INFO] Row{} not in between ball and goal, move to default position".format(row))
	# 			players[row].center()
	#
	#
	# # Opponent is in control of ball and the ball is not moving towards our goal
	# elif fb.controllingRow in [2, 4, 6, 7]:
	#
	# 	# Reset counter
	# 	idleFrames = 0
	#
	# 	# Move all rows to default defensive position
	# 	for row in [0, 1, 3, 5]:
	# 		players[row].center()
	#
	#
	# # TODO: build out based on scenario
	# # For now, we basically just calculate the angle between current position and the opponent's goal, and shoot
	# # We are in control of ball and there is a direct or indirect opening between ball and opponent goal
	# # We are in control of ball, no path exists, and our offense is in control of ball
	# # We are in control of ball, no path exists, and our midfield is in control of ball
	# # We are in control of ball, no path exists, and our defense is in control of ball
	# # We are in control of ball, no path exists, and our goalie is in control of ball
	# elif fb.controllingRow in [0, 1, 3, 5]:
	#
	# 	# Reset counter
	# 	idleFrames = 0
	#
	# 	# Make sure ball will be ahead of players on next frame
	# 	if fb.projectedPosition[0] >= fb.vars["rowPosition"][fb.controllingRow]:
	#
	# 		# Calculate optimal angle between ball and opponent's goal
	# 		tempX = fb.vars["width"] - fb.ballPositions[-1:][0][0]
	# 		tempY = fb.vars["height"] / 2 - fb.ballPositions[-1:][0][1]
	#
	# 		# Calculate arc tangent (in radians) and convert to degrees
	# 		angle = math.atan2(tempX, tempY) / math.pi * 180
	#
	# 		fb.log("[INFO] Row{} kick towards opponent goal at angle {}".format(fb.controllingRow, angle))
	# 		players[fb.controllingRow].kickAngle(angle, tempX, tempY)
	#
	# 	else:
	# 		fb.log("[INFO] Row{} pause, since ball will not be ahead of row on next frame".format(fb.controllingRow))
	#
	#
	# # Neither player is in control of the ball
	# elif fb.controllingRow is -1:
	#
	# 	# Increment counter
	# 	idleFrames = idleFrames + 1
	#
	# 	# If the number of idle frames exceeds threshold, pause game and show warning/error message
	# 	if idleFrames > 100:
	# 		fb.log("[INFO] Number of idle frames exceeds threshold, end game")
	# 		fb.gameIsActive = False
	#
	#
	# # Something went wrong
	# else:
	# 	fb.log("[INFO] Controlling row: {}".format(fb.controllingRow))
	# 	fb.log("[INFO] Something went wrong... exiting now")
	# 	fb.gameIsActive = False


	fb.log("[INFO] Main loop end", True)


# Stop timer and display FPS information
print()
print("Ending Main Script")
print("Elapsed time: {:.2f}".format(fb.elapsedTime))
print("Avg FPS: {:.2f}".format(fb.fps))
print()

# Release motors
for row in players:
	if row is not None:
		row.stop()


# Do a bit of cleanup
# Reset GPIO, stop camera, video file, and destroy all windows
io.cleanup()
cv2.destroyAllWindows()
if writer is not None:
	writer.release()
vs.stop()
