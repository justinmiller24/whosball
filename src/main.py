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

print("Starting Main Script")


# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("--debug", help="whether or not to show debug mode", action="store_true")
ap.add_argument("--output", help="path to output video file")
args = vars(ap.parse_args())


##########################################################################
# This section initializes the camera, video, foosball table, and motors #
##########################################################################

# Initialize camera and allow time to warm up
vs = videoStream().start()
time.sleep(2.0)

# Initialize foosball game
fb = foosball(args["debug"]).start()

# Record video output to file
writer = None
if args["output"]:
	h = fb.vars["height"] * 2 + (20 * 3) + (8 * 2)
	w = fb.vars["width"] * 2 + 8
	fourcc = cv2.VideoWriter_fourcc('M','J','P','G')
	writer = cv2.VideoWriter(args["output"], fourcc, 30, (w, h), True)


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

	# Only continue if the location of the foosball is known. One note, this
	# includes "projected" coordinates in the event that the ball is occluded.
	if fb.foosballPosition is None:
		fb.log("[INFO] No projected position, continue loop")
		continue

	# At this point, we can calculate the most likely position of the ball in the next frame
	projectedX = fb.getProjectedX()


	##########################################################################
	# This section rotates the forward rows UP or DOWN depending on location #
	##########################################################################

	# The foosball is behind the midfield row
	if projectedX < fb.vars["foosmenRED"][2]:
		fb.log("[INFO] Ball is behind midfield row")
		fb.log("[MOTOR] Move midfield row and offense row UP")
		#if fb.motor3.isPositionDown or fb.motor4.isPositionDown:
			#fb.motor3.setPositionUp()
			#fb.motor4.setPositionUp()
			#time.sleep(2.0)

	# The foosball is between the midfield row and the offense row
	elif projectedX < fb.vars["foosmenRED"][3]:
		fb.log("[INFO] Ball is between midfield row and offense row")
		fb.log("[MOTOR] Move midfield row DOWN and intercept")

		# Intercept with midfield row
		#fb.motor3.intercept(getPositionHere...)

		#if fb.motor3.isPositionUp or fb.motor4.isPositionDown:
			#fb.motor3.setPositionDown()
			#fb.motor4.setPositionUp()
			#time.sleep(2.0)

	# The foosball is ahead of the offense row
	else:
		fb.log("[INFO] Ball is ahead of offense row")
		fb.log("[MOTOR] Move midfield row and offense row DOWN and intercept")

		# Intercept with offense row
		#fb.motor4.intercept(getPositionHere...)

		#if fb.motor3.isPositionUp or fb.motor4.isPositionUp:
			#fb.motor3.setPositionDown()
			#fb.motor4.setPositionDown()
			#time.sleep(2.0)


	##########################################################################
	# This section determines which row is in control of the ball,           #
	# calculates the position(s) required for each row,                      #
	# detemines the amount of movement needed for each motor,                #
	# and moves the motors based on the desired position/reaction            #
	##########################################################################

	# Find out which foosmen row is most likely to control the ball next
	closestRow = fb.getClosestRow(projectedX)

	# Goalie
	if closestRow == 0 and projectedX >= fb.vars["foosmenRED"][0]:
		fb.log("[INFO] Goal row is in control of the ball")
		fb.log("[MOTOR] Goal row KICK!")
		#fb.motor1.kick()

	# Defense
	elif closestRow == 1 and projectedX >= fb.vars["foosmenRED"][1]:
		fb.log("[INFO] Defense row is in control of the ball")
		fb.log("[MOTOR] Defense row KICK!")
		#fb.motor2.kick()

	# Midfield
	elif closestRow == 3 and projectedX >= fb.vars["foosmenRED"][2]:
		fb.log("[INFO] Midfield row is in control of the ball")
		fb.log("[MOTOR] Midfield row KICK!")
		#fb.motor3.kick()

	# Offense
	elif closestRow == 5 and projectedX >= fb.vars["foosmenRED"][3]:
		fb.log("[INFO] Offense row is in control of the ball")
		fb.log("[MOTOR] Offense row KICK!")
		#fb.motor3.kick()


	##########################################################################
	# This section moves the defensive rows laterally to intercept the ball  #
	##########################################################################

	#fb.motor1.intercept(getPositionHere...)
	#fb.motor2.intercept(getPositionHere...)
	#c.move(3,(yInterceptPosition / pixelsPerInch) - 8.75);


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
	fb.buildOutputFrame()
	cv2.imshow("Output", fb.outputImg)
	if cv2.waitKey(1) & 0xFF == ord("q"):
		break

	# Write frame to output file
	if writer is not None:
		writer.write(fb.outputImg)


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
