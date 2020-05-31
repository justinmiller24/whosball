#########################
# Automated Foosball    #
#########################

# USAGE
# python test.py

# import the necessary packages
import argparse
import cv2
import time
from camera import videoStream
from foosball import Foosball
from players import Foosmen


##########################################################################
# This section initializes the camera, foosball table, and motors        #
##########################################################################

# Initialize camera and allow time to warm up
print("Initialize camera")
vs = videoStream().start()
time.sleep(2.0)

# Initialize foosball game
print("Initialize game")
fb = Foosball(False).start()

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

# Find location of the foosball
fb.findBall()

# Find location of the players
fb.findPlayers("RED")
fb.findPlayers("BLUE")


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

# Save frame to file
cv2.imwrite("test.png", out)

# Do a bit of cleanup
# Stop camera, video file, and destroy all windows
cv2.destroyAllWindows()
vs.stop()
