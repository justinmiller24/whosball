from adafruit_motorkit import MotorKit
from collections import deque
import cv2
import cv2.aruco as aruco
import datetime
import math
import numpy as np
import time


class foosball:

    # Initialize table
    def __init__(self, debug=False):

        self.debug = debug

        # Create a dictionary with pre-calculated values for faster lookup
        # Attributes prefixed with an underscore (_) are needed for calculation only
        self.dim = {

            # The foosball table measures 46.75" (length) x 26.5" (width)
            # This is 118.745cm (width) x 67.31cm (height), based on our camera
            '_maxWidth': 118.75,                    # Table length (in cm)
            '_maxHeight': 67.31,                    # Table width (in cm)

            # This is an aspect ratio of 1.76 which is about 16x9
            # We will convert all frames to 640px x 360px for processing
            'xPixels': 640,                         # Max width (in pixels)
            #'xPixels': 320,                         # Max width (in pixels)
            'yPixels': 360,                         # Max height (in pixels)
            #'yPixels': 180,                         # Max height (in pixels)

            # The number of pixels per cm is constant (640 px / 118.745 cm)
            # This means 5.39 pixels represents 1 cm of actual distance on the table
            'pxPerCm': 5.39,                        # Pixels per cm (ratio)

            # The width of each goal is about 6 3/4" at the point where a foosball would pass
            '_goalWidth': 92.41,                    # Goal width (in pixels)

            # Each "goal boundary" is calculated from the middle of the table +/- 1/2 of the goal width
            # ie, the lower bound = pxPerCm * ((maxHeight - goalWidth) / 2)
            # ie, the upper bound = pxPerCm * (maxHeight - ((maxHeight - goalWidth) / 2))
            'goalLower': 133.79,                    # Lower boundary of goal (in pixels)
            'goalUpper': 226.20,                    # Upper boundary of goal (in pixels)

            # The foosball measures 1 3/8" in diameter
            'foosballWidth': 18,                    # Foosball width and height (rounded down, in pixels)
            'foosballHSVLower': (15, 0, 0),         # Foosball lower bound (HSV)
            'foosballHSVUpper': (35, 255, 255),     # Foosball upper bound (HSV)
            'foosballMaxPositions' 30,              # The maximum number of "coordinates" to track

            # There are 8 foosball rods, each one measures 5/8" in diameter
            # The total distance across all 8 rods is 40 7/16"
            # This means the distance between two rods is 40 7/16" / (8 - 1) * 2.54 * pxPerCm
            '_rodWidth': 8.55,                      # Foosball rod width (in pixels)
            '_rodSpacing': 79.09,                   # Foosball rod spacing (in pixels)

            # Each foosmen rod has a bumper on each end that measures 1 1/4" in width
            # This creates a "space" and is the minimum between each end foosmen and the wall
            'rodMargin': 17,                        # Foosmen rod bumper (rounded down, in pixels)

            # The rods are centered on the table, so we calculate the x coordinate of each rod
            # The rods take up a total width of (rodSpacing * (numRods - 1) + rodWidth)
            # So there is (tableWidth - totalRodWidth) / 2 width between each goal and the end rod
            # Total rod spacing = (640px - (79.09 * 7 + 8.55)) / 2 = 38.91px (on each end)
            # The first rod is located at 38.91px + (rodWidth / 2) = 43.185px
            # Each additional rod is located an additional "rodSpacing" (79.09px) apart
            'rodPosition': [43.19, 122.28, 201.37, 280.46, 359.55, 438.64, 517.73, 596.82],
            'foosmenRED': np.array([43.19, 122.28, 280.46, 438.64], dtype="float32"),
            'foosmenBLUE': np.array([201.37, 359.55, 517.73, 596.82], dtype="float32"),

            # The foosmen are centered on each rod, but each rod (row) has a different number of men
            # There are 13 total foosmen, each with a unique ID from left to right and top to bottom
            # Each foosmen kicks the ball with feet that measure 1" in width
            'foosmenWidth': 14,                     # Foosmen width (rounded up, in pixels)
            'foosmenHeight': 36,                    # Foosmen height (how far they "span" in either direction)

            # RED players
            'foosmenRedHSVLower': (170, 0, 0),      # Foosmen lower bound (HSV)
            'foosmenRedHSVUpper': (180, 255, 255),  # Foosmen upper bound (HSV)
            'foosmenRedContour': (255, 100, 100),   # Foosmen contour highlight color
            'foosmenRedBox': (255, 0, 0),           # Foosmen bounding box color

            # BLUE players
            'foosmenBlueHSVLower': (85, 0, 0),      # Foosmen lower bound (HSV)
            'foosmenBlueHSVUpper': (110, 255, 255), # Foosmen upper bound (HSV)
            'foosmenBlueContour': (100, 100, 255),  # Foosmen contour highlight color
            'foosmenBlueBox': (0, 0, 255),          # Foosmen bounding box color

            # The first row (goalie) has 3 men, spaced 7 1/8" apart, and 8 1/2" of linear movement
            # The second row (defense) has 2 men, spaced 9 5/8" apart, and 13 3/8" of linear movement
            # The third row (midfield) has 5 men, spaced 5" apart, and 4 1/4" of linear movement
            # The fourth row (offense) has 3 men, spaced 7 1/8" apart, and 8 1/2" of linear movement
            '_row0': (97.54, 116.37),               # Spacing, linear movement (in pixels)
            '_row1': (131.77, 183.11),              # Spacing, linear movement (in pixels)
            '_row2': (68.45, 58.18),                # Spacing, linear movement (in pixels)
            '_row3': (97.54, 116.37),               # Spacing, linear movement (in pixels)

            # Calculate the lower and upper bounds for each foosmen
            'foosmen': np.array([
                # Goalie
                (17, 148),                          # Min/max coordinates (in pixels)
                (115, 246),                         # Min/max coordinates (in pixels)
                (212, 343),                         # Min/max coordinates (in pixels)
                # Defense
                (17, 211),                          # Min/max coordinates (in pixels)
                (149, 343),                         # Min/max coordinates (in pixels)
                # Midfield
                (17, 69),                           # Min/max coordinates (in pixels)
                (85, 137),                          # Min/max coordinates (in pixels)
                (154, 206),                         # Min/max coordinates (in pixels)
                (222, 274),                         # Min/max coordinates (in pixels)
                (291, 343),                         # Min/max coordinates (in pixels)
                # Offense
                (17, 148),                          # Min/max coordinates (in pixels)
                (115, 246),                         # Min/max coordinates (in pixels)
                (212, 343),                         # Min/max coordinates (in pixels)
            ])
        }
        if self.debug:
            self.log(self.dim)

        # Motors and Motor Limits
        # This is the maximum position for the motors in each rod
        #test = {'linearMotor': None, 'rotationalMotor': None, 'linearMotorLimit': None}

        self.motors = np.array([])
        #for i in range(4):
            #self.motors = np.append(self.motors, {
                #'linearMotor': None,
                #'linearMotorLimit': self.dim['_maxHeight'] - (self.foosmen[i]['players'] - 1) * self.foosmen[i]['spacing'] - 2 * self.table['margin'],
                #'rotationalMotor': None,
            #})

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

        # Track frames and time so that we can display FPS
        self.startTime = None
        self.currentTime = None
        self.elapsedTime = 0
        self.numFrames = 0
        self.fps = None

        if self.debug:
            self.log("[STATUS] Initialize Table")
            self.log("[STATUS] Game Is Active: {}".format(self.gameIsActive))
            self.log("[STATUS] Ball Is In Play: {}".format(self.ballIsInPlay))


    # Start game
    def start(self):
        if self.debug:
            self.log("[DEBUG] Start function begin")

        # Initialize motors and all I/O ports
        # This includes calibration of the motors for linear and rotational motion
        #self.motors = None

        # Initialize goal interrupt service routine (ISR)
        # If a goal is detected, this helps us keep track of score and reset for the next ball drop
        #self.goalDetect = False

        # Initialize table coordinates
        # Define coordinates for foosball table in top-left, top-right, bottom-left, and bottom-right order
        tL = (73,130)
        tR = (557,136)
        bR = (561,414)
        bL = (59,405)
        self.tableCoords = [tL, tR, bR, bL]
        self.origCoords = None

        # Start game
        self.gameIsActive = True
        self.ballIsInPlay = False

        # History of foosball position/coordinates
        self.ballPositions = []
        self.projectedPosition = None

        # Initialize score to 0-0
        self.score = (0, 0)

        # Start timer
        self.startTime = datetime.datetime.now()

        if self.debug:
            self.log("[DEBUG] Start function end")

        return self


    # Add current foosball position and calculate motion
    def _addCurrentPosition(self, pos):

        # Reset counter of how many frames the foosball has been undetected
        self.lostBallFrames = 0

        # Add current foosball position to array, and make sure we have no more than X items
        self.ballPositions.append(pos)
        if len(self.ballPositions) > self.dim["foosballMaxPositions"]:
            self.ballPositions.pop(0)

        # Make sure we have at least 3 points to perform calculations
        if len(self.ballPositions) < 3:
            return

        # Previous ball position
        #lastPosition = self.ballPositions[-2:][0]
        #origX = lastPosition[0]
        #origY = lastPosition[1]

        # Current ball position
        #currPosition = self.ballPositions[-1:][0]
        #destX = currPosition[0]
        #destY = currPosition[1]

        # Deltas
        #deltaX = destX - origX
        #deltaY = destY - origY


        # Calculate motion and projected trajectory based on the last 3 coordinates
        #prevX, prevY = self.ballPositions[-3:][0]
        #currX, currY = self.ballPositions[-1:][0]

        # Use average of the last 2 x/y slopes
        self.deltaX = (self.ballPositions[-1:][0][0] - self.ballPositions[-3:][0][0]) / 2
        self.deltaY = (self.ballPositions[-1:][0][1] - self.ballPositions[-3:][0][1]) / 2

        # Ignore unless there is "significant" movement
        if abs(self.deltaX) + abs(self.deltaY) < 2:
            self.log("[TRACKING] Ignore insignificant movement for projected positions")
            self.deltaX = 0
            self.deltaY = 0

        # Calculate projected next coordinate
        self.projectedPosition = [self.ballPositions[-1:][0][0] + self.deltaX, self.ballPositions[-1:][0][1] + self.deltaY]
        self.log("[TRACKING] Projected next position is: {}".format(self.projectedPosition))

        # Project goal on next frame
        if self.projectedPosition[0] < 0:
            self.log("[TRACKING] Projected Goal: WHOSBALL Player")
        elif self.projectedPosition[0] > self.dim["xPixels"]:
            self.log("[TRACKING] Projected Goal: Human Player")

        # Calculate distance (in cm), velocity, and direction -- for visual display only
        distancePX = math.sqrt(self.deltaX * self.deltaX + self.deltaY * self.deltaY)
        self.distance = distancePX / self.dim["pxPerCm"]

        # Velocity
        # Use FPS if avaialble, otherwise default to 30fps
        distanceM = self.distance / 100
        if self.fps:
            self.velocity = distanceM / (1 / self.fps)
        else:
            self.velocity = distanceM / (1 / 30)

        # Direction
        # Calculate number degrees between two points
        # Calculate arc tangent (in radians) and convert to degrees
        degrees_temp = math.atan2(self.deltaX, self.deltaY) / math.pi * 180
        if degrees_temp < 0:
            self.degrees = 360 + degrees_temp
        else:
            self.degrees = degrees_temp


    # Function to update video display
    def buildOutputFrame(self):
        if self.debug:
            self.log("[DEBUG] Update display begin")

        images = [self.frame, self.mask3, self.contoursImg, self.outputImg]


        # Grab dimensions of first image
        (h, w) = images[0].shape[:2]

        # Build multiview display
        padW = 8
        padH = 20
        mvHeight = (h * 2) + (padH * 3) + (padW * 2)
        mvWidth = w * 2 + padW
        out = np.zeros((mvHeight, mvWidth, 3), dtype="uint8")

        # Top Left
        cv2.putText(out, "Original", (w // 2 - 35, 15), cv2.FONT_HERSHEY_PLAIN, 1, (255, 255, 255), 1)
        out[padH:h+padH, 0:w] = images[0]

        # Top Right
        cv2.putText(out, "Mask", (w + w // 2 - 30, 15), cv2.FONT_HERSHEY_PLAIN, 1, (255, 255, 255), 1)
        out[padH:h+padH, w+padW:w*2+padW] = images[1]

        # Bottom Left
        cv2.putText(out, "Contours", (w // 2 - 35, 20+h+3+15), cv2.FONT_HERSHEY_PLAIN, 1, (255, 255, 255), 1)
        out[h+3+padH+padH:h*2+3+padH+padH, 0:w] = images[2]

        # Bottom Right
        cv2.putText(out, "Final", (w + w // 2 - 30, 20+h+3+15), cv2.FONT_HERSHEY_PLAIN, 1, (255, 255, 255), 1)
        out[h+3+padH+padH:h*2+3+padH+padH, w+padW:w*2+padW] = images[3]

        # Bottom
        cDisplay = ("{}".format(self.foosballPosition)) if self.foosballPosition is not None else "-"
        rDisplay = ("%2.1f" % self.radius) if self.radius is not None else "-"
        dDisplay = ("%2.1f cm" % self.distance) if self.distance is not None else "-"
        aDisplay = ("%2.1f" % self.degrees) if self.degrees is not None else "-"
        vDisplay = ("%2.1f m/s" % self.velocity) if self.velocity is not None else "-"
        fDisplay = ("%2.1f" % self.fps) if self.fps is not None else "-"
        cv2.putText(out, "Center: %s" % cDisplay, (90, mvHeight - 5), cv2.FONT_HERSHEY_PLAIN, 1, (255, 255, 255), 1)
        cv2.putText(out, "Radius: %s" % rDisplay, (290, mvHeight - 5), cv2.FONT_HERSHEY_PLAIN, 1, (255, 255, 255), 1)
        cv2.putText(out, "Distance: %s" % dDisplay, (420, mvHeight - 5), cv2.FONT_HERSHEY_PLAIN, 1, (255, 255, 255), 1)
        cv2.putText(out, "Direction: %s" % aDisplay, (620, mvHeight - 5), cv2.FONT_HERSHEY_PLAIN, 1, (255, 255, 255), 1)
        cv2.putText(out, "Velocity: %s" % vDisplay, (820, mvHeight - 5), cv2.FONT_HERSHEY_PLAIN, 1, (255, 255, 255), 1)
        cv2.putText(out, "FPS: %s" % fDisplay, (1020, mvHeight - 5), cv2.FONT_HERSHEY_PLAIN, 1, (255, 255, 255), 1)

        if self.debug:
            self.log("[DEBUG] Update display end")

        return out


    # Determine if a goal was scored or not
    def _checkForGoal(self):
        if self.debug:
            self.log("[DEBUG] Check for goal begin")

        # An actual goal can only happen once
        if self.lostBallFrames > 1:
            return

        # Check for score
        # Use average of the last 2 x/y slopes
        lastKnownX = self.ballPositions[-1:][0][0]
        lastProjectedX = self.projectedPosition[0]

        # Computer Goal
        if lastKnownX < 10 and lastProjectedX < 10:
            self.log("[TRACKING] Goal for WHOSBALL Player")
            self.goalScored = True
            self.ballIsInPlay = False

        # Human Goal
        elif lastKnownX > self.dim["xPixels"] - 10 and lastProjectedX > self.dim["xPixels"] - 10:
            self.log("[TRACKING] Goal for Human Player")
            self.goalScored = True
            self.ballIsInPlay = False

        # No Goal
        else:
            self.log("[TRACKING] No Goal Scored for either player")
            self.goalScored = False
            self.ballIsInPlay = True

        self.log("[DEBUG] Goal Scored: {}".format(self.goalScored))
        self.log("[DEBUG] Ball Is In Play: {}".format(self.ballIsInPlay))

        if self.debug:
            self.log("[DEBUG] Check for goal end")

        return self.goalScored


    # Take current image, perform object recognition,
    # and convert this information into the coordinate of the foosball
    def detectFoosball(self):
        if self.debug:
            self.log("[DEBUG] Detect Foosball begin")

        origImg = self.frame.copy()
        self.outputImg = self.frame.copy()

        # HSV, Grayscale, Edges
        self.blurred = cv2.GaussianBlur(origImg, (11, 11), 0)
        self.hsv = cv2.cvtColor(self.blurred, cv2.COLOR_BGR2HSV)
        #gray = cv2.cvtColor(origImg, cv2.COLOR_RGB2GRAY)
        #self.gray3 = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

        # Create mask and perform morphological "opening" to remove small blobs in mask.
        # Opening erodes an image and then dilates the eroded image, using the same structuring
        # element for both operations. This is useful for removing small objects from an image
        # while preserving the shape and size of larger objects in the image.
        mask = cv2.inRange(self.hsv, self.dim["foosballHSVLower"], self.dim["foosballHSVUpper"])
        mask = cv2.erode(mask, None, iterations=4)
        mask = cv2.dilate(mask, None, iterations=4)
        self.mask3 = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)

        # Find contours in mask and initialize the current center (x, y) of the ball
        cnts = self._getContours(mask)

        # Iterate through contours and filter by the number of vertices
        (h, w) = origImg.shape[:2]
        self.contoursImg = np.zeros((h, w, 3), dtype="uint8")
        for c in cnts:
            #perimeter = cv2.arcLength(c, True)
            epsilon = 0.04 * cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, epsilon, True)
            #if len(approx) > 5:
            cv2.drawContours(self.contoursImg, [c], -1, (36, 255, 12), -1)

        self.radius = None
        self.distance = None
        self.degrees = None
        self.velocity = None

        # Ensure at least one contour was found
        if len(cnts) > 0:

            self.foosballDetected = True
            self.ballIsInPlay = True

            # Find the largest contour in the mask and use this to
            # compute the minimum enclosing circle and centroid
            c = max(cnts, key=cv2.contourArea)
            ((x, y), self.radius) = cv2.minEnclosingCircle(c)
            M = cv2.moments(c)
            foosballPosition = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
            self.log("[STATUS] Foosball detected: {}".format(foosballPosition))

            # Add current position to the list of tracked points
            self._addCurrentPosition(foosballPosition)

            # Draw centroid
            cv2.circle(self.outputImg, foosballPosition, 5, (0, 0, 255), -1)

            # Update list of tracked points
            #self._updateTrackedPoints()

        # Foosball was not detected as a recognized object. This is either because:
        #   1) The foosball was not in play previously
        #   2) The foosball was in play and a goal just occurred
        #   3) The foosball is still in play but is occluded
        #   4) Our object detection algorithm is not working correctly
        else:
            self.foosballDetected = False

            # Increase counter of how many frames the foosball has been undetected
            self.lostBallFrames += 1

            # Check for case #1 -- the foosball was not in play previously
            # If this is the case, there's probably nothing else to do until the next play starts
            if not self.ballIsInPlay:
                self.log("[STATUS] The ball was not in play previously, continue with loop...")
                self.ballIsInPlay = False
                return

            # At this point, we know the ball was in play previously
            # Check for case #2 -- the foosball was in play previously and a goal just occurred
            if self._checkForGoal():
                self.log("[STATUS] The ball was in play and it looks like a goal occurred!")

                # Update score

                self.ballIsInPlay = False
                return

            # At this point, we know the ball is likely occluded
            self.log("[STATUS] The ball is likely occluded. Determine projected coordinates.")

        self.log("[STATUS] Num contours found: {}".format(len(cnts)))
        self.log("[STATUS] Foosball detected: {}".format(self.foosballDetected))
        self.log("[STATUS] Foosball position: {}".format(self.foosballPosition))
        self.log("[STATUS] Foosball in play: {}".format(self.ballIsInPlay))

        if self.debug:
            self.log("[DEBUG] Detect Foosball end")


    # Take current image, perform object recognition,
    # and convert this information into the coordinates of the RED and BLUE players
    def detectPlayers(self, mode):
        if self.debug:
            self.log("[DEBUG] Detect players begin")

        # Set variables based on mode (RED or BLUE)
        if mode == "RED":
            foosmenRows = self.dim["foosmenRED"]
            hsvLower = self.dim["foosmenRedHSVLower"]
            hsvUpper = self.dim["foosmenRedHSVUpper"]
            contourRGB = self.dim["foosmenRedContour"]
            rectangleRGB = self.dim["foosmenRedBox"]
        elif mode == "BLUE":
            foosmenRows = self.dim["foosmenBLUE"]
            hsvLower = self.dim["foosmenBlueHSVLower"]
            hsvUpper = self.dim["foosmenBlueHSVUpper"]
            contourRGB = self.dim["foosmenBlueContour"]
            rectangleRGB = self.dim["foosmenBlueBox"]
        else:
            self.log("[ERROR] _getMaskForPlayers has invalid value for mode")
            return

        # Get mask and apply mask to image
        # Create mask containing "only" the areas with the rods for RED/BLUE foosmen
        # TODO: Reduce processing time by moving the "mask creation" to init() function, since it does not need to be recreated every frame
        origImg = self.frame.copy()
        playerMask = self._getMaskForPlayers(foosmenRows)
        maskedImg = cv2.bitwise_and(origImg, playerMask)

        # Create mask based on HSV range for foosmen
        blurred = cv2.GaussianBlur(maskedImg, (11, 11), 0)
        hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

        # Create color mask for foosmen and perform erosions and dilation to remove small blobs in mask
        mask = cv2.inRange(hsv, hsvLower, hsvUpper)
        mask = cv2.erode(mask, None, iterations=4)
        mask = cv2.dilate(mask, None, iterations=4)
        #self.foosmenMask = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)

        # Detect foosmen using contours
        players = self._getContours(mask)

        #if mode == "RED":
            #self.playersRed = players
        #elif mode == "BLUE":
            #self.playersBlue = players

        # Overlay contour and rectangle over each player
        self.playersImg = np.zeros((self.dim["yPixels"], self.dim["xPixels"], 3), dtype="uint8")
        for i in players:

            # Get coordinates of bounding rectangle and draw rectangle on output image
            x, y, w, h = cv2.boundingRect(i)
            cv2.drawContours(self.playersImg, [i], -1, contourRGB, -1)
            cv2.rectangle(self.playersImg, (x, y), (x + w, y + h), rectangleRGB, 2)

        if self.debug:
            self.log("[DEBUG] Detect players end")


    # Detect ArUco markers and transform perspective
    # This effectively crops the frame to just show the foosball table
    def detectTable(self):
        if self.debug:
            self.log("[DEBUG] Detect table begin")

        origImg = self.rawFrame.copy()

        # Detect markers
        # `corners` is the list of corners returned in clockwise order: top left, top right, bottom right, bottom left
        # `ids` is a list of marker IDs of each of the detected markers
        gray = cv2.cvtColor(origImg, cv2.COLOR_BGR2GRAY)
        arucoDict = aruco.Dictionary_get(aruco.DICT_4X4_50)
        arucoParameters =  aruco.DetectorParameters_create()
        corners, ids, rejectedImgPoints = aruco.detectMarkers(gray, arucoDict, parameters=arucoParameters)
        #print(ids)

        # Display detected markers
        if ids is not None:
            self.log("[STATUS] ArUco markers detected:")
            self.log(ids)
            #output = aruco.drawDetectedMarkers(output, corners, ids)

            # Default to existing coordinates
            #tL, tR, bR, bL = self.tableCoords

            # Top Left
            #if ids[0]:
                #marker = np.squeeze(corners[0])
                #x, y = marker[0]
                #tL = (x, y)
                #if self.debug:
                    #self.log("[DEBUG] ArUco Marker exists in Top Left")
                    #self.log(tL)

            # Top Right
            #if ids[1]:
                #marker = np.squeeze(corners[1])
                #x, y = marker[1]
                #tR = (x, y)
                #if self.debug:
                    #self.log("[DEBUG] ArUco Marker exists in Top Right")
                    #self.log(tR)

            # Bottom Right
            #if ids[2]:
                #marker = np.squeeze(corners[2])
                #x, y = marker[2]
                #bR = (x, y)
                #if self.debug:
                    #self.log("[DEBUG] ArUco Marker exists in Bottom Right")
                    #self.log(bR)

            # Bottom Left
            #if ids[3]:
                #marker = np.squeeze(corners[3])
                #x, y = marker[3]
                #bL = (x, y)
                #if self.debug:
                    #self.log("[DEBUG] ArUco Marker exists in Bottom Left")
                    #self.log(bL)

            #self.tableCoords = [tL, tR, bR, bL]
            if self.debug:
                self.log("[STATUS] Table boundaries (tL, tR, bR, bL):")
                self.log(self.tableCoords)
            #for i in range(0, len(ids)):
                #id = str(ids[i][0])

                #marker = np.squeeze(corners[i])

                #x0, y0 = marker[0]
                #x2, y2 = marker[2]
                #x = int((x0 + x2)/2)
                #y = int((y0 + y2)/2)

                #result.add((id, x, y))
        else:
            self.log("[ERROR] No ArUco markers detected, use defaults")

        # Apply projective transformation (also known as "perspective transformation" or "homography") to the
        # original image. This type of transformation was chosen because it preserves straight lines.
        # To do this, we first compute the transformational matrix (M) and then apply it to the original image.
        # The resulting frame will have an aspect ratio identical to the size (in pixels) of the foosball playing field
        w = self.dim['xPixels']
        h = self.dim['yPixels']
        self.origCoords = np.array(self.tableCoords, dtype="float32")
        finalCoords = np.array([(0,0), (w-1,0), (w-1,h-1), (0,h-1)], dtype="float32")
        M = cv2.getPerspectiveTransform(self.origCoords, finalCoords)
        self.frame = cv2.warpPerspective(origImg, M, (w, h))

        if self.debug:
            self.log("[DEBUG] Detect table end")

        return self.frame


    def determineMotorMovement(self):
        if self.debug:
            self.log("[DEBUG] Determine motor movement begin")
            self.log("[DEBUG] Determine motor movement end")


    def determineTrackingMethod(self):
        if self.debug:
            self.log("[DEBUG] Determine tracking method begin")

        self.trackingMethod = "Defense"

        self.log("[STATUS] Tracking method: {}".format(self.trackingMethod))

        if self.debug:
            self.log("[DEBUG] Determine tracking method end")

        return self.trackingMethod


    def foosmenTakeover(self):
        if self.debug:
            self.log("[DEBUG] Foosmen takeover begin")
            self.log("[DEBUG] Foosmen takeover end")


    # Get contours
    def _getContours(self, mask):

        # Detect object using contours
        cnts = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Extract contours depending on the OpenCV version
        # Copied from https://github.com/jrosebr1/imutils/blob/master/imutils/convenience.py
        if len(cnts) == 2:
            if self.debug:
                self.log("[REMOVE THIS] Using OpenCV 2.4 or 4.x")
            cnts = cnts[0]
        # if the length of the contours tuple is '3' then we are using
        # either OpenCV v3, v4-pre, or v4-alpha
        elif len(cnts) == 3:
            if self.debug:
                self.log("[REMOVE THIS] Using OpenCV 3.x or v4pre/alpha")
            cnts = cnts[1]
        else:
            self.log("[ERROR] _getContours function did not return the correct result")

        return cnts


    # Get mask for RED or BLUE players based on foosmenRows array
    def _getMaskForPlayers(self, foosmenRows):
        if self.debug:
            self.log("[DEBUG] Get Mask for Mode begin")

        mask = np.zeros((self.dim["yPixels"], self.dim["xPixels"], 3), dtype="uint8")

        # Add "whitelabel" mask for each rod containing foosmen with matching color
        for rod in foosmenRows:
            # Create "vertical strips" that are 2 x "foosmenHeight" pixels wide, spanning entire frame (0 to yMax height)
            cv2.rectangle(mask, (int(rod - self.dim["foosmenHeight"]), 0), (int(rod + self.dim["foosmenHeight"]), self.dim["yPixels"]), (255, 255, 255), -1)
        mask = cv2.resize(mask, mask.shape[1::-1])

        if self.debug:
            self.log("[DEBUG] Get Mask for Mode end")

        return mask


    # Determine which foosmen row is closest to the foosball
    def _getClosestRow(self, x):
        closestRow = 0
        min = self.dim.["xPixels"]

        # Loop through foosball rows and determine which is closest to X-coordinate of the foosball's current position
        for row in range(self.dim["rodPosition"]):
            if abs(self.dim["rodPosition"][row] - x) < min:
                min = abs(self.dim["rodPosition"][row] - x)
                closestRow = row

        return closestRow


    # Get motor with position "i"
    def getMotor(self, i):
        if self.debug:
            self.log("[DEBUG] Get Motor [{}]".format(i))

        return self.motors[i]


    # Linear interpolation between two points (x1, y1) and (x2, y2) and evaluates
    # the function at point xi
    def interpolate(self, xi, x2, y2, x1, y1):
        if self.debug:
            self.log("[DEBUG] Interpolate begin")

        ret = (xi - x1) * (y2 - y1) / (x2 - x1) + y1

        if self.debug:
            self.log("[DEBUG] Interpolate end")

        return ret


    # Print output message to console
    def log(self, msg):
        print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"), msg)


    # Move MotorKit motors
    # https://learn.adafruit.com/adafruit-dc-and-stepper-motor-hat-for-raspberry-pi/using-stepper-motors
    def moveMotors(self):
        if self.debug:
            self.log("[DEBUG] Move motors begin")
            self.log("[DEBUG] Move motors end")

        #self.motors.kit1.stepper1.onestep()


    # Save new frame and update FPS data
    def readFrame(self, frame):
        if self.debug:
            self.log("[DEBUG] Read frame begin")

        self.rawFrame = frame

        # Calculate updated FPS
        self.numFrames += 1
        self.currentTime = datetime.datetime.now()
        self.elapsedTime = (self.currentTime - self.startTime).total_seconds()
        self.fps = self.numFrames / self.elapsedTime

        if self.debug:
            self.log("[DEBUG] Read frame end")


    # Show trailing list of tracked points
    #def _updateTrackedPoints(self):

        # Add latest point to list of tracked points
        #self.pts.appendleft(self.foosballPosition)

        # loop over the set of tracked points
        #for i in range(1, len(self.pts)):

        	# if either of the tracked points are None, ignore them
        	#if self.pts[i - 1] is None or self.pts[i] is None:
        		#continue

        	# otherwise, compute the thickness of the line and draw the connecting lines
        	#thickness = int(np.sqrt(30 / float(i + 1)) * 2.5)
        	#cv2.line(self., self.pts[i - 1], self.pts[i], (0, 0, 255), thickness)
