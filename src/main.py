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
print("Initialize players and motors")
# Goalie
# The 1st row has 3 men, spaced 7 1/8" apart, and 8 1/2" of linear movement
#f0 = Foosmen(0, 3, fb.vars["row0"][0], fb.vars["row0"][1], fb.vars["foosmenWidth"]).start()
# Defense
# The 2nd row has 2 men, spaced 9 5/8" apart, and 13 3/8" of linear movement
#f1 = Foosmen(1, 2, fb.vars["row1"][0], fb.vars["row1"][1], fb.vars["foosmenWidth"]).start()
# Midfield
# The 3rd row has 5 men, spaced 5" apart, and 4 1/4" of linear movement
#f3 = Foosmen(3, 5, fb.vars["row2"][0], fb.vars["row2"][1], fb.vars["foosmenWidth"]).start()
# Offense
# The 4th row has 3 men, spaced 7 1/8" apart, and 8 1/2" of linear movement
#f5 = Foosmen(5, 3, fb.vars["row3"][0], fb.vars["row3"][1], fb.vars["foosmenWidth"]).start()

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


	##########################################################################
	# Display to screen and record video output                              #
	##########################################################################

	# Display original (uncropped) image and transformation coordinates
	origImg = fb.rawFrame.copy()
	if fb.origCoords is not None:
		for (x, y) in fb.origCoords:
			cv2.circle(origImg, (x, y), 5, (0, 255, 0), -1)
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
	# This section determines how to respond based on current conditions.    #
	# We attempt a DEFENSIVE strategy first. If no possibilities exist here, #
	# then attempt an OFFENSIVE strategy. If no possibilities exist here,    #
	# then we continue in a HOLDING pattern until something changes.         #
	##########################################################################
	#
	# Assumptions:
	# - We know where the table, foosball, and players currently are
	# - The foosball can be controlled by only row at a time, at most
	# - We are able to move all 4 rows in both axes (linear and rotational) simultaneously
	#
	# DEFENSE
	# 1. Direct or indirect (bounce) shot on goal
	#    a. For all rows in between ball and goal, if they can intercept, move to intercept
	#    b. For all rows in between ball and goal, if they can not intercept, leave still
	#    c. For all rows not in between ball and goal, assume default defensive position (see #3)
	# 2. Direct or indirect (bounce) shot moving towards us
	#    a. For all rows in between ball and path of ball, find the closest row that can intercept, and intercept
	#    b. For all other rows (not the closest row), assume default defensive position (see #3)
	# 3. Other player is in control of the ball (this is the "default" defensive position)
	#    a. Goalie moves to middle of goal
	#    b. 2-rod moves to either just above/below goalie, depending on yPos of ball
	#    c. Midfield moves to block man-to-man with opponent's midfield row
	#    d. Offense
	#       i. If ball is controlled by their defense, our offense attempts to block the ball (same yPos as ball)
	#       ii. Otherwise, move offensive to center position
	#
	# OFFENSE
	# 4. Determine controlling row and move controlling row to ball
	# 5. There is a direct or indirect (bounce) path between ball and opponent's goal
	#    a. Shoot in direct or indirect (bounce) path towards opponent's goal
	#    b. Move any rows in between shooting row and opponent's goal out of the way (so we don't block our own shot)
	#    c. All other rows assume default defensive position (see #3)
	# 6. There is not a direct path between ball and opponent's goal, and our offense is in control
	#    a. Randomly select one of the following:
	#       i. Attempt lateral pass to next player and move player to receive
	#       ii. Determine widest opening between opponent's 2-rod/goalie and goal, and attempt pass to intercepting point
	#       iii. Take shot on goal anyway
	#    b. All other rows assume default defensive position (see #3)
	# 7. There is not a direct path between ball and opponent's goal, and our midfield is in control
	#    a. Determine widest opening between opponent's midfielders
	#    b. Attempt pass between widest opening
	#    c. Move offensive row to receive pass at intercepting point
	#    d. All other rows assume default defensive position (see #3)
	# 8. There is not a direct path between ball and opponent's goal, and our goalie or 2-rod is in control
	#    a. Determine widest opening between opponent's offensive players
	#    b. Attempt pass between widest opening
	#    c. Move midfield row to receive pass at intercepting point
	#    d. All other rows assume default defensive position (see #3)
	#
	# HOLDING
	# 9. Neither player is in control of the ball
	#    a. Reset / increment timer to track number of frames
	# 10. If we hit a certain threshold, pause game and show warning/error for user to intervene
	#
	##########################################################################




	# Check if the ball is coming towards us
	#if fb.deltaX < 0:

		# Check if ball is heading towards the LEFT wall
		#if fb.projectedWallPosition[0] = 0:

			# Check for shot on goal
			# We calculate this if the LEFT wall is the next intersecting wall
			# and the intersecting point is between the bounds of the goal
			#if fb.projectedWallPosition[1] > fb.vars["goalLower"] and fb.projectedWallPosition[1] < fb.vars["goalUpper"]:
				#fb.log("[INFO] Shot on goal. All rows block if possible!")

				# If the ball is heading towards our goal, find out how many more frames before the ball reaches our goal
				#numFramesUntilGoal = fb.currentPosition[0] // fb.deltaX

				# Move goalie to block
				#f0.moveTo(fb.projectedWallPosition[1])

				# Move defense to block, if needed
				#if fb.currentPosition[0] > fb.vars["foosmenRED"][1]:
					#f1.moveTo(fb.getIntersectingCoordinate(fb.vars["foosmenRED"][1])

				# Move midfielders to block, if needed
				#if fb.currentPosition[0] > fb.vars["foosmenRED"][2]:
					#f2.moveTo(fb.getIntersectingCoordinate(fb.vars["foosmenRED"][2])

				# Move offense to block, if needed
				#if fb.currentPosition[0] > fb.vars["foosmenRED"][3]:
					#f3.moveTo(fb.getIntersectingCoordinate(fb.vars["foosmenRED"][3])


			# There is not a shot on goal, so this means it will hit the back wall
			#else:
				#fb.log("[INFO] Shot towards back wall. Applicable rows try to block.")


		# The ball is coming towards us, but will not hit the back wall, so it will
		# either hit the TOP or BOTTOM wall. Check for this and determine how it will bounce
		#elif fb.projectedWallPosition[1] = 0 or fb.projectedWallPosition[1] == fb.vars["height"]:
		#else:
			#fb.log("[INFO] Shot towards TOP or BOTTOM wall. Determine bounce coordinates and attempt to block.")




	##########################################################################
	#  Find out which row is in control of the ball,                         #
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
		#f0.rotateTo(75)

	# Defense
	elif closestRow == 1 and projectedX >= fb.vars["foosmenRED"][1]:
		fb.log("[INFO] Defense row is in control of the ball")
		fb.log("[MOTOR] Defense row KICK!")
		#f1.rotateTo(75)

	# Midfield
	elif closestRow == 3 and projectedX >= fb.vars["foosmenRED"][2]:
		fb.log("[INFO] Midfield row is in control of the ball")
		fb.log("[MOTOR] Midfield row KICK!")
		#f3.rotateTo(75)

	# Offense
	elif closestRow == 5 and projectedX >= fb.vars["foosmenRED"][3]:
		fb.log("[INFO] Offense row is in control of the ball")
		fb.log("[MOTOR] Offense row KICK!")
		#f5.rotateTo(75)


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
