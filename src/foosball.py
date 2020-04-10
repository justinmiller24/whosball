from adafruit_motorkit import MotorKit
from collections import deque
import cv2
import datetime
import imutils
import math
import numpy as np
import time


class foosball:

    # Initialize table
    def __init__(self, debug=False):

        self.debug = debug

        # Pre-calculate dimensions for table, foosmen, foosball, rods, etc
        # Store these for faster lookup, to reduce the amount of overhead required while playing
        self.table = {

            # Foosball Table - 26.5" x 46.75"
            # Resulting frame should have an aspect ratio around 510px x 297px
            'xPixels': 510,         # Image width (table length) in pixels
            'yPixels': 297,         # Image height (table width) in pixels
            'xMax': 116.8,        # Table length (in cm)
            'yMax': 68,           # Table width (in cm)
            'margin': 1.75,       # Min distance between foosmen and the wall
            'rows': np.empty(8),  # X coordinate of each foosball rod (8 total)
        }
        # Row Positions ("x" coordinates)
        for i in range(8):
            self.table['rows'][i] = (2 * i + 1) * self.table['xMax'] / 16
            #self.table['rows'][0] = 1 * self.table['xMax'] / 16     # Row 1
            #self.table['rows'][1] = 3 * self.table['xMax'] / 16     # Row 2
            #etc...

        # Goal
        goalWidth = 18.5
        self.goal = {
            'width': goalWidth,
            'limits': [0.5 * (self.table['yMax'] - goalWidth), 0.5 * (self.table['yMax'] - goalWidth) + goalWidth]
        }

        # Foosmen and Maximum Position of Foosmen
        self.foosmen = np.array([
            {'limits': np.empty(3), 'players': 3, 'spacing': 18.3},    # Goalie
            {'limits': np.empty(2), 'players': 2, 'spacing': 24.5},    # Defense
            {'limits': np.empty(5), 'players': 5, 'spacing': 12.0},    # Midfield
            {'limits': np.empty(3), 'players': 3, 'spacing': 18.5},    # Offense
        ])
        # Row 0 - Goalie
        #self.foosmen[0]['limits'][0] = [self.table['margin'] + 0 * self.foosmen[0]['spacing'], self.table['yMax'] - (self.table['margin'] + 2 * self.foosmen[0]['spacing'])]
        #self.foosmen[0]['limits'][1] = [self.table['margin'] + 1 * self.foosmen[0]['spacing'], self.table['yMax'] - (self.table['margin'] + 1 * self.foosmen[0]['spacing'])]
        #self.foosmen[0]['limits'][2] = [self.table['margin'] + 2 * self.foosmen[0]['spacing'], self.table['yMax'] - (self.table['margin'] + 0 * self.foosmen[0]['spacing'])]
        # Row 1 - Defense
        #self.foosmen[1]['limits'][0] = [self.table['margin'] + 0 * self.foosmen[1]['spacing'], self.table['yMax'] - (self.table['margin'] + 1 * self.foosmen[1]['spacing'])]
        #self.foosmen[1]['limits'][1] = [self.table['margin'] + 1 * self.foosmen[1]['spacing'], self.table['yMax'] - (self.table['margin'] + 0 * self.foosmen[1]['spacing'])]
        # Row 2 - Midfield
        #self.foosmen[2]['limits'][0] = [self.table['margin'] + 0 * self.foosmen[2]['spacing'], self.table['yMax'] - (self.table['margin'] + 4 * self.foosmen[2]['spacing'])]
        #self.foosmen[2]['limits'][1] = [self.table['margin'] + 1 * self.foosmen[2]['spacing'], self.table['yMax'] - (self.table['margin'] + 3 * self.foosmen[2]['spacing'])]
        #self.foosmen[2]['limits'][2] = [self.table['margin'] + 2 * self.foosmen[2]['spacing'], self.table['yMax'] - (self.table['margin'] + 2 * self.foosmen[2]['spacing'])]
        #self.foosmen[2]['limits'][3] = [self.table['margin'] + 3 * self.foosmen[2]['spacing'], self.table['yMax'] - (self.table['margin'] + 1 * self.foosmen[2]['spacing'])]
        #self.foosmen[2]['limits'][4] = [self.table['margin'] + 4 * self.foosmen[2]['spacing'], self.table['yMax'] - (self.table['margin'] + 0 * self.foosmen[2]['spacing'])]
        # Row 3 - Offense
        #self.foosmen[3]['limits'][0] = [self.table['margin'] + 0 * self.foosmen[3]['spacing'], self.table['yMax'] - (self.table['margin'] + 2 * self.foosmen[3]['spacing'])]
        #self.foosmen[3]['limits'][1] = [self.table['margin'] + 1 * self.foosmen[3]['spacing'], self.table['yMax'] - (self.table['margin'] + 1 * self.foosmen[3]['spacing'])]
        #self.foosmen[3]['limits'][2] = [self.table['margin'] + 2 * self.foosmen[3]['spacing'], self.table['yMax'] - (self.table['margin'] + 0 * self.foosmen[3]['spacing'])]

        # Motors and Motor Limits
        # This is the maximum position for the motors in each rod
        #test = {'linearMotor': None, 'rotationalMotor': None, 'linearMotorLimit': None}

        self.motors = np.array([])
        for i in range(4):
            self.motors = np.append(self.motors, {
                'linearMotor': None,
                'linearMotorLimit': self.table['yMax'] - (self.foosmen[i]['players'] - 1) * self.foosmen[i]['spacing'] - 2 * self.table['margin'],
                'rotationalMotor': None,
            })

        # Initialize the 1st hat on the default address (0x60)
        # Initialize the 2nd hat on the default address (0x61)
        # Initialize the 3rd hat on the default address (0x63)
        # Initialize the 4th hat on the default address (0x67)

        # Stepper motors are available as stepper1 and stepper2
        # stepper1 is made up of the M1 and M2 terminals
        # stepper2 is made up of the M3 and M4 terminals
        #self.motors[0]['linearMotor'] = MotorKit().stepper1
        #self.motors[0]['rotationalMotor'] = MotorKit().stepper2
        #self.motors[1]['linearMotor'] = MotorKit(address=0x61).stepper1
        #self.motors[1]['rotationalMotor'] = MotorKit(address=0x61).stepper2
        #self.motors[2]['linearMotor'] = MotorKit(address=0x63).stepper1
        #self.motors[2]['rotationalMotor'] = MotorKit(address=0x63).stepper2
        #self.motors[3]['linearMotor'] = MotorKit(address=0x67).stepper1
        #self.motors[3]['rotationalMotor'] = MotorKit(address=0x67).stepper2

        # Tracking Methods
        self.trackingMethods = ['Offense', 'Defense']
        self.trackingMethod = "Defense"

        # Variable to determine if a game is currently in progress or not
        # This can be toggled at any time to STOP or PAUSE play
        self.gameIsActive = False
        self.ballIsInPlay = False

        if self.debug:
            self.log("Initialize Table")
            self.log("Game Is Active: {}".format(self.gameIsActive))
            self.log("Ball Is In Play: {}".format(self.ballIsInPlay))


    # Start game
    def start(self):
        if self.debug:
            self.log("Start function called")

        # Initialize motors and all I/O ports
        # This includes calibration of the motors for linear and rotational motion
        #self.motors = None

        # Initialize goal interrupt service routine (ISR)
        # If a goal is detected, this helps us keep track of score and reset for the next ball drop
        #self.goalDetect = False

        # Start game
        self.gameIsActive = True
        self.ballIsInPlay = False

        # Track history of ball position
        # Initialize ball position array
        self.ball_position_history = []
        # Initialize list of tracked points
        self.pts = deque(maxlen=30)

        # Initialize score to 0-0
        self.score = (0, 0)

        return self


    # Calculate motion of foosball based on history
    def calculateFoosballMotion(self):
        if self.debug:
            self.log("Calculate foosball motion function")

        # Make sure we have at least two points to perform motion calculations
        if len(self.ball_position_history) < 2:
            if self.debug:
                self.log("Cannot calculate motion -- need at least two points")
                return

        # Last ball position
        lastPosition = self.ball_position_history[-2:][0]
        origX = lastPosition[0]
        origY = lastPosition[1]

        # Current ball position
        currPosition = self.ball_position_history[-1:][0]
        destX = currPosition[0]
        destY = currPosition[1]

        # Deltas
        deltaX = destX - origX
        deltaY = destY - origY

        # Distance
        distancePX = math.sqrt(deltaX * deltaX + deltaY * deltaY)
        #self.distanceCM = self.distancePX / ratio_pxcm
        #self.distanceM = self.distanceCM / 100
        self.distance = distancePX

        # Velocity
        #self.velocity = self.distance / frame_time

        # Direction
        # Calculate number degrees between two points
        # Calculate arc tangent (in radians) and convert to degrees
        degrees_temp = math.atan2(deltaX, deltaY) / math.pi * 180
        if degrees_temp < 0:
            self.degrees = 360 + degrees_temp
        else:
            self.degrees = degrees_temp


    # Check if a goal occurred
    def checkForGoal(self):
        if self.debug:
            self.log("Check to see if a score occurred")

        goalScored = False
        if goalScored:
            self.log("Goal Scored!")
            self.ballIsInPlay = False

        return goalScored


    # Take current image, perform object recognition,
    # and convert this information into the coordinate of the foosball
    def detectFoosball(self, ballMin1HSV, ballMax1HSV, ballMin2HSV, ballMax2HSV):
        if self.debug:
            self.log("Detect Foosball function called")

        origImg = self.frame.copy()
        self.finalImg = self.frame.copy()

        # HSV, Grayscale, Edges
        self.blurred = cv2.GaussianBlur(origImg, (11, 11), 0)
        self.hsv = cv2.cvtColor(self.blurred, cv2.COLOR_BGR2HSV)
        #gray = cv2.cvtColor(origImg, cv2.COLOR_RGB2GRAY)
        #self.gray3 = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

        # Blob detection
        # Set our filtering parameters
        # Initialize parameter settiing using cv2.SimpleBlobDetector
        #blobImg = self.hsv.copy()
        #params = cv2.SimpleBlobDetector_Params()

        # Set Area filtering parameters
        #params.filterByArea = True
        #params.minArea = 100

        # Set Circularity filtering parameters
        #params.filterByCircularity = True
        #params.minCircularity = 0.9

        # Set Convexity filtering parameters
        #params.filterByConvexity = True
        #params.minConvexity = 0.2

        # Set inertia filtering parameters
        #params.filterByInertia = True
        #params.minInertiaRatio = 0.01

        # Create a detector with the parameters
        #detector = cv2.SimpleBlobDetector_create(params)

        # Detect blobs
        #keypoints = detector.detect(blobImg)

        # Draw blobs on our image as red circles
        #blank = np.zeros((1, 1))
        #blobs = cv2.drawKeypoints(blobImg, keypoints, blank, (0, 0, 255), cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)

        #number_of_blobs = len(keypoints)
        #text = "Number of Circular Blobs: " + str(len(keypoints))
        #cv2.putText(blobImg, text, (20, 550), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 100, 255), 2)

        # Create color mask for foosball and perform erosions and dilation to remove small blobs in mask
        mask1 = cv2.inRange(self.hsv, ballMin1HSV, ballMax1HSV)
        mask2 = cv2.inRange(self.hsv, ballMin2HSV, ballMax2HSV)
        mask = cv2.bitwise_or(mask1, mask2)
        mask = cv2.erode(mask, None, iterations=2)
        mask = cv2.dilate(mask, None, iterations=2)
        self.mask3 = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)

        # Find contours in mask and initialize the current center (x, y) of the ball
        cnts = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        # Extract contours depending on OpenCV version
        cnts = imutils.grab_contours(cnts)

        # Iterate through contours and filter by the number of vertices
        (h, w) = origImg.shape[:2]
        self.contoursImg = np.zeros((h, w, 3), dtype="uint8")
        for c in cnts:
        	perimeter = cv2.arcLength(c, True)
        	approx = cv2.approxPolyDP(c, 0.04 * perimeter, True)
        	if len(approx) > 5:
        		cv2.drawContours(self.contoursImg, [c], -1, (36, 255, 12), -1)

        self.center = None
        self.radius = None
        self.distance = None
        self.degrees = None
        #self.velocity = None

        # Ensure at least one contour was found
        if len(cnts) > 0:
            self.foosballDetected = True
            self.ballIsInPlay = True

            # Find the largest contour in the mask and use this to
            # compute the minimum enclosing circle and centroid
            c = max(cnts, key=cv2.contourArea)
            ((x, y), self.radius) = cv2.minEnclosingCircle(c)
            M = cv2.moments(c)
            self.center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
            if self.debug:
                self.log("Foosball Position: (%s, %s)".format(self.center))

            # Add to list of tracked points
            self.ball_position_history.append(self.center)

            # Calculate motion of foosball
            self.calculateFoosballMotion()

            # Draw centroid
            cv2.circle(self.finalImg, self.center, 5, (0, 0, 255), -1)

            # Update list of tracked points
            self.updateTrackedPoints()

        # Foosball was not detected as a recognized object. This is either because:
        #   1) The foosball was not in play previously
        #   2) The foosball was in play and a goal just occurred
        #   3) The foosball is still in play but is occluded
        #   4) Our object detection algorithm is not working correctly
        else:
            self.foosballDetected = False

            # Check for case #1 -- the foosball was not in play previously
            # If this is the case, there's probably nothing else to do until the next play starts
            if not self.ballIsInPlay:
                self.log("The ball was not in play previously, continue with loop...")
                self.ballIsInPlay = False
                return

            # At this point, we know the ball was in play previously
            # Check for case #2 -- the foosball was in play previously and a goal just occurred
            if self.goalScored():
                self.log("The ball was in play and it looks like a goal occurred!")

                # Determine who scored

                # Update score

                self.ballIsInPlay = False
                return

            # At this point, we know the ball is likely occluded


    # Take current image, perform object recognition,
    # and convert this information into the coordinates of the RED and BLUE players
    def detectPlayers(self):
        if self.debug:
            self.log("Detect RED and BLUE players")


    def determineMotorMovement(self):
        if self.debug:
            self.log("Determine which motors to move")


    def determineTrackingMethod(self):
        if self.debug:
            self.log("Determine tracking method")

        self.trackingMethod = "Defense"

        if self.debug:
            self.log("Tracking method is {}".format(self.trackingMethod))

        return self.trackingMethod


    def foosmenTakeover(self):
        if self.debug:
            self.log("Calculate if takeover is needed")


    # Check if foosball game is in progress
    #def gameIsInProgress(self):
        #return self.gameIsActive


    # Get motor with position "i"
    def getMotor(self, i):
        if self.debug:
            self.log("Get Motor [{}]".format(i))

        return self.motors[i]


    # Get current game score
    def getScore(self):
        return self.score


    # Linear interpolation between two points (x1, y1) and (x2, y2) and evaluates
    # the function at point xi
    def interpolate(self, xi, x2, y2, x1, y1):
        return (xi - x1) * (y2 - y1) / (x2 - x1) + y1


    # Print output message to console
    def log(self, msg):
        print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"), msg)


    # Move MotorKit motors
    # https://learn.adafruit.com/adafruit-dc-and-stepper-motor-hat-for-raspberry-pi/using-stepper-motors
    def moveMotors(self):
        if self.debug:
            self.log("Move motors")

        #self.motors.kit1.stepper1.onestep()


    # Set next frame
    def setRawFrame(self, frame):
        if self.debug:
            self.log("Set next frame")

        self.rawFrame = frame


    #def toggleDebugMode(self):
        #self.debug = not self.debug
        #self.log("Debug Mode is now:", self.debug)


    # Apply homography and transform perspective of image
    def transformImagePerspective(self, coords):
        origImg = self.rawFrame.copy()
        self.origCoords = np.array(coords, dtype="float32")

        # Compute perspective transformation matrix
        tableW = self.table['xPixels']
        tableH = self.table['yPixels']
        finalCoords = np.array([(0,0), (tableW-1,0), (0,tableH-1), (tableW-1,tableH-1)], dtype="float32")
        M = cv2.getPerspectiveTransform(self.origCoords, finalCoords)

        # Apply perspective transformation matrix to image
        # The resulting frame will have an aspect ratio identical to the size (in pixels) of the foosball playing field
        self.frame = cv2.warpPerspective(origImg, M, (tableW, tableH))

        return self.frame


    # Function to update video display
    def updateDisplay(self, images):

        if self.debug:
            self.log("Update multi view display")

        # Display original (uncropped) image
        # Show transformation coordinates on original image
        origImg = self.rawFrame.copy()
        for (x, y) in self.origCoords:
            cv2.circle(origImg, (x, y), 5, (0, 255, 0), -1)
        cv2.namedWindow("Raw")
        cv2.moveWindow("Raw", 1250, 100)
        cv2.imshow("Raw", origImg)

        # Grab dimensions of first image
        (h, w) = images[0].shape[:2]

        # Build multiview display
        padW = 8
        padH = 20
        mvHeight = (h * 2) + (padH * 3) + (padW * 2)
        mvWidth = w * 2 + padW
        self.output = np.zeros((mvHeight, mvWidth, 3), dtype="uint8")

        # Top Left
        cv2.putText(output, "Original", (w // 2 - 35, 15), cv2.FONT_HERSHEY_PLAIN, 1, (255, 255, 255), 1)
        self.output[padH:h+padH, 0:w] = images[0]

        # Top Right
        cv2.putText(output, "Mask", (w + w // 2 - 30, 15), cv2.FONT_HERSHEY_PLAIN, 1, (255, 255, 255), 1)
        self.output[padH:h+padH, w+padW:w*2+padW] = images[1]

        # Bottom Left
        cv2.putText(output, "Contours", (w // 2 - 35, 20+h+3+15), cv2.FONT_HERSHEY_PLAIN, 1, (255, 255, 255), 1)
        self.output[h+3+padH+padH:h*2+3+padH+padH, 0:w] = images[2]

        # Bottom Right
        cv2.putText(output, "Final", (w + w // 2 - 30, 20+h+3+15), cv2.FONT_HERSHEY_PLAIN, 1, (255, 255, 255), 1)
        self.output[h+3+padH+padH:h*2+3+padH+padH, w+padW:w*2+padW] = images[3]

        # Bottom
        cDisplay = ("{}".format(self.center)) if self.center is not None else "-"
        rDisplay = ("%2.1f" % self.radius) if self.radius is not None else "-"
        dDisplay = ("%2.1f" % self.distance) if self.distance is not None else "-"
        aDisplay = ("%2.1f" % self.degrees) if self.degrees is not None else "-"
        vDisplay = "-"
        cv2.putText(self.output, "Center: %s" % cDisplay, (90, mvHeight - 5), cv2.FONT_HERSHEY_PLAIN, 1, (255, 255, 255), 1)
        cv2.putText(self.output, "Radius: %s" % rDisplay, (290, mvHeight - 5), cv2.FONT_HERSHEY_PLAIN, 1, (255, 255, 255), 1)
        cv2.putText(self.output, "Distance: %s" % dDisplay, (420, mvHeight - 5), cv2.FONT_HERSHEY_PLAIN, 1, (255, 255, 255), 1)
        cv2.putText(self.output, "Direction: %s" % aDisplay, (620, mvHeight - 5), cv2.FONT_HERSHEY_PLAIN, 1, (255, 255, 255), 1)
        cv2.putText(self.output, "Velocity: %s" % vDisplay, (820, mvHeight - 5), cv2.FONT_HERSHEY_PLAIN, 1, (255, 255, 255), 1)

        # Show display on screen
        cv2.imshow("Output", self.output)


    # Show trailing list of tracked points
    def updateTrackedPoints(self):
        if self.debug:
            self.log("Update tracked points")

        # Add latest point to list of tracked points
        self.pts.appendleft(self.center)

        # loop over the set of tracked points
        for i in range(1, len(self.pts)):

        	# if either of the tracked points are None, ignore them
        	if self.pts[i - 1] is None or self.pts[i] is None:
        		continue

        	# otherwise, compute the thickness of the line and draw the connecting lines
        	thickness = int(np.sqrt(30 / float(i + 1)) * 2.5)
        	cv2.line(self.finalImg, self.pts[i - 1], self.pts[i], (0, 0, 255), thickness)
