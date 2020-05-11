#########################
# Automated Foosball    #
#########################

# import the necessary packages
import cv2
import cv2.aruco as aruco
import datetime
import math
import numpy as np
import time


class Foosball:

    # Initialize table
    def __init__(self, debug=False):

        self.debug = debug

        # Create a dictionary with pre-calculated values for faster lookup
        # Attributes prefixed with an underscore (_) are needed for calculation only
        self.vars = {

            # The foosball table measures 46.75" (length) x 26.5" (width)
            # This is 118.745cm (width) x 67.31cm (height), based on our camera
            '_maxWidth': 118.75,                    # Table length (in cm)
            '_maxHeight': 67.31,                    # Table width (in cm)

            # This is an aspect ratio of 1.76 which is about 16x9
            # We will convert all frames to 640px x 360px for processing
            'width': 640,                           # Table width (in pixels) -- this is the x max
            'height': 360,                          # Table height (in pixels) -- this is the y max

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
            'foosballMaxPositions': 30,             # The maximum number of "coordinates" to track

            # There are 8 foosball rods, each one measures 5/8" in diameter
            # The total distance across all 8 rods is 40 7/16"
            # This means the distance between two rods is 40 7/16" / (8 - 1) * 2.54 * pxPerCm
            '_rowWidth': 8.55,                      # Foosball rod width (in pixels)
            '_rowSpacing': 79.09,                   # Foosball rod spacing (in pixels)

            # Each foosmen rod has a bumper on each end that measures 1 1/4" in width
            # This creates a "space" and is the minimum between each end foosmen and the wall
            'rowMargin': 17,                        # Foosmen rod bumper (rounded down, in pixels)

            # The rods are centered on the table, so we calculate the x coordinate of each rod
            # The rods take up a total width of (rodSpacing * (numRods - 1) + rodWidth)
            # So there is (tableWidth - totalRodWidth) / 2 width between each goal and the end rod
            # Total rod spacing = (640px - (79.09 * 7 + 8.55)) / 2 = 38.91px (on each end)
            # The first rod is located at 38.91px + (rodWidth / 2) = 43.185px
            # Each additional rod is located an additional "rodSpacing" (79.09px) apart
            'rowPosition': [43.19, 122.28, 201.37, 280.46, 359.55, 438.64, 517.73, 596.82],
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
            'row0': (97.54, 116.37),                # Spacing, linear movement (in pixels)
            'row1': (131.77, 183.11),               # Spacing, linear movement (in pixels)
            'row2': (68.45, 58.18),                 # Spacing, linear movement (in pixels)
            'row3': (97.54, 116.37),                # Spacing, linear movement (in pixels)

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
            self.log(self.vars)

        # Variable to determine if a game is currently in progress or not
        # This can be toggled at any time to STOP or PAUSE play
        self.gameIsActive = False
        self.ballIsInPlay = False
        self.foosballDetected = False

        # Track frames and time so that we can display FPS
        self.startTime = None
        self.currentTime = None
        self.elapsedTime = 0
        self.numFrames = 0
        self.fps = None


    # Start game
    def start(self):

        # Initialize table coordinates
        # Define coordinates for foosball table in top-left, top-right, bottom-left, and bottom-right order
        tL = (73,130)
        tR = (557,136)
        bR = (561,414)
        bL = (59,405)
        self.tableCoords = [tL, tR, bR, bL]
        self.origCoords = None

        # Create foosmen "masks" for RED and BLUE players
        # We do this once, so that we don't need to recalculate it on every single frame
        self.vars["foosmenREDMask"] = self._getMaskForPlayers(self.vars["foosmenRED"])
        self.vars["foosmenBLUEMask"] = self._getMaskForPlayers(self.vars["foosmenBLUE"])

        # Start game
        self.gameIsActive = True
        self.ballIsInPlay = False
        self.foosballDetected = False

        # History of foosball position/coordinates
        self.ballPositions = []
        self.lostBallFrames = 0
        self.foosballPosition = None
        self.projectedPosition = None

        # Initialize score to 0-0
        self.score = [0, 0]

        # Start timer
        self.startTime = datetime.datetime.now()

        return self


    # Add current foosball position and calculate motion
    def _addCurrentPosition(self, pos):

        # Reset counter of how many frames the foosball has been undetected
        self.lostBallFrames = 0

        # Add current foosball position to array, and make sure we have no more than X items
        self.ballPositions.append(pos)
        if len(self.ballPositions) > self.vars["foosballMaxPositions"]:
            self.ballPositions.pop(0)

        # If this is the first point, then the next projected position will be the same as the current point
        if len(self.ballPositions) < 2:
            if self.debug:
                self.log("[DEBUG] We only have one point. Projected position will be the same.")
            self.deltaX = 0
            self.deltaY = 0

        # If we only have two points, then calculate deltas between the last 2 known points
        elif len(self.ballPositions) < 3:
            self.deltaX = (self.ballPositions[-1:][0][0] - self.ballPositions[-2:][0][0]) / 1
            self.deltaY = (self.ballPositions[-1:][0][1] - self.ballPositions[-2:][0][1]) / 1

        # Otherwise, calculate deltas based on last 3 known points
        else:
            self.deltaX = (self.ballPositions[-1:][0][0] - self.ballPositions[-3:][0][0]) / 2
            self.deltaY = (self.ballPositions[-1:][0][1] - self.ballPositions[-3:][0][1]) / 2

        # Ignore deltas unless there is "significant" movement
        if abs(self.deltaX) + abs(self.deltaY) < 2:
            if self.debug:
                self.log("[DEBUG] Ignore insignificant movement for projected positions")
            self.deltaX = 0
            self.deltaY = 0

        # Calculate which wall the ball will hit next, assuming it continues uninterrupted
        else:
            self._getIntersectingWallPosition()
            if self.projectedWallPosition is not None:
                self.log("[INFO] Intersecting wall coordinates: {}".format(self.projectedWallPosition))
            else:
                self.log("[ERROR] SOMETHING WENT WRONG!!! Need to update formula.")

        # Calculate projected next coordinate
        self.projectedPosition = [self.ballPositions[-1:][0][0] + self.deltaX, self.ballPositions[-1:][0][1] + self.deltaY]
        self.log("[INFO] Projected next position is: {}".format(self.projectedPosition))

        # Project goal on next frame
        if self.projectedPosition[0] < 0:
            self.log("[INFO] Projected Goal: WHOSBALL Player")
        elif self.projectedPosition[0] > self.vars["width"]:
            self.log("[INFO] Projected Goal: Human Player")

        # Calculate distance (in cm), velocity, and direction -- for visual display only
        distancePX = math.sqrt(self.deltaX * self.deltaX + self.deltaY * self.deltaY)
        self.distance = distancePX / self.vars["pxPerCm"]

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
        #degrees_temp = math.atan2(self.deltaX, self.deltaY) / math.pi * 180
        #if degrees_temp < 0:
            #self.degrees = 360 + degrees_temp
        #else:
            #self.degrees = degrees_temp


    # Function to update video display
    def buildOutputFrame(self):
        if self.debug:
            self.log("[DEBUG] Update display begin")

        # Build output
        out = np.zeros((self.vars["height"] + 144, self.vars["width"], 3), dtype="uint8")
        vPos = self.vars["height"] + 5

        # Output image
        out[0:self.vars["height"], 0:self.vars["width"]] = self.outputImg

        # Key metrics
        metrics = {
            "Score": self.score,
            "In Play": self.ballIsInPlay,
            "Detected": self.foosballDetected,
            "Position": ("{}".format(self.foosballPosition)) if self.foosballPosition is not None else "-",
            #"Projected": self.projectedPosition,
            "Radius": ("%2.1f" % self.radius) if self.radius is not None else "-",
            #"Distance": ("%2.1f cm" % self.distance) if self.distance is not None else "-",
            "Velocity": ("%2.1f m/s" % self.velocity) if self.velocity is not None else "-",
            "FPS": ("%2.1f" % self.fps) if self.fps is not None else "-",
        }
        for key in metrics:
            vPos += 18
            cv2.putText(out, "%s: %s" % (key, metrics[key]), (10, vPos), cv2.FONT_HERSHEY_PLAIN, 1, (255, 255, 255), 1)

        if self.debug:
            self.log("[DEBUG] Update display end")

        return out


    # Determine if a goal was scored or not
    def _checkForGoal(self):

        # An actual goal can only happen once
        if self.lostBallFrames > 1:
            return False

        # An actual goal likely requires some kind of projected position
        lastProjectedX = self.getProjectedX()
        if lastProjectedX is None:
            if self.debug:
                self.log("[DEBUG] Projected Position is None, it is unlikely a goal was scored")
            return False

        # Make sure Y-coordinate is between the upper/lower bounds of goal
        lastProjectedY = self.projectedPosition[1]
        if lastProjectedY < self.vars["goalLower"] or lastProjectedY > self.vars["goalUpper"]:
            if self.debug:
                self.log("[DEBUG] Projected Y coordinate is not within goal lower/upper bounds")
            return False

        # Check for score
        lastKnownX = self.ballPositions[-1:][0][0]

        # Computer Goal
        if lastKnownX < 10 and lastProjectedX < 10:
            self.score[0] += 1
            self.log("[INFO] Goal for WHOSBALL Player, score is now: {}".format(self.score))
            return True

        # Human Goal
        elif lastKnownX > self.vars["width"] - 10 and lastProjectedX > self.vars["width"] - 10:
            self.score[1] += 1
            self.log("[INFO] Goal for Human Player, score is now: {}".format(self.score))
            return True

        # No Goal
        else:
            if self.debug:
                self.log("[DEBUG] No goal scored for either player")

        return False


    # Take current image, perform object recognition,
    # and convert this information into the coordinate of the foosball
    def findBall(self):
        if self.debug:
            self.log("[DEBUG] Detect Foosball begin")

        # If the foosball was previously detected, localize the search to save overall computation time
        if self.foosballDetected:
            self.log("[INFO] TODO: Foosball was previously detected. Localize search to save time here...")

        origImg = self.frame.copy()
        self.outputImg = self.frame.copy()

        # Convert to HSV color range
        self.blurred = cv2.GaussianBlur(origImg, (11, 11), 0)
        self.hsv = cv2.cvtColor(self.blurred, cv2.COLOR_BGR2HSV)

        # Create mask and perform morphological "opening" to remove small blobs in mask.
        # Opening erodes an image and then dilates the eroded image, using the same structuring
        # element for both operations. This is useful for removing small objects from an image
        # while preserving the shape and size of larger objects in the image.
        mask = cv2.inRange(self.hsv, self.vars["foosballHSVLower"], self.vars["foosballHSVUpper"])
        mask = cv2.erode(mask, None, iterations=4)
        mask = cv2.dilate(mask, None, iterations=4)
        #self.mask3 = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)

        # Find contours in mask and initialize the current center (x, y) of the ball
        cnts = self._getContours(mask)

        # Find and display contours
        (h, w) = origImg.shape[:2]
        #self.outputImg = np.zeros((h, w, 3), dtype="uint8")
        for c in cnts:
            #perimeter = cv2.arcLength(c, True)
            epsilon = 0.04 * cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, epsilon, True)
            #if len(approx) > 5:
            cv2.drawContours(self.outputImg, [c], -1, (36, 255, 12), -1)

        self.radius = None
        self.distance = None
        #self.degrees = None
        self.velocity = None

        # Ensure at least one contour was found
        self.log("[INFO] Contours found: {}".format(len(cnts)))
        if len(cnts) > 0:

            self.foosballDetected = True
            self.ballIsInPlay = True

            # Find the largest contour in the mask and use this to
            # compute the minimum enclosing circle and centroid
            c = max(cnts, key=cv2.contourArea)
            ((x, y), self.radius) = cv2.minEnclosingCircle(c)
            M = cv2.moments(c)
            self.foosballPosition = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))

            # Add current position to the list of tracked points
            self._addCurrentPosition(self.foosballPosition)

            # Draw centroid
            cv2.circle(self.outputImg, self.foosballPosition, 5, (0, 0, 255), -1)

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
            self.log("[INFO] Number of lost ball frames: {}".format(self.lostBallFrames))

            # Check for case #1 -- the foosball was not in play previously
            # If this is the case, there's probably nothing else to do until the next play starts
            if not self.ballIsInPlay:
                self.log("[INFO] The ball was not in play previously, continue with loop")
                return

            # At this point, we know the ball was in play previously
            # Check for case #2 -- the foosball was in play previously and a goal just occurred
            elif self._checkForGoal():
                self.log("[INFO] The ball was in play and it looks like a goal occurred!")

            # At this point, we know the ball is likely occluded
            else:
                self.log("[INFO] The ball is likely occluded. Last known projected coordinates: {}".format(self.projectedPosition))

        self.log("[INFO] Foosball detected: {}".format(self.foosballDetected))
        self.log("[INFO] Foosball position: {}".format(self.foosballPosition))
        self.log("[INFO] Projected position: {}".format(self.projectedPosition))

        if self.debug:
            self.log("[DEBUG] Detect Foosball end")


    # Take current image, perform object recognition,
    # and convert this information into the coordinates of the RED and BLUE players
    def findPlayers(self, mode):
        if self.debug:
            self.log("[DEBUG] Detect players begin")

        # Set variables based on mode (RED or BLUE)
        if mode == "RED":
            foosmenMask = self.vars["foosmenREDMask"]
            hsvLower = self.vars["foosmenRedHSVLower"]
            hsvUpper = self.vars["foosmenRedHSVUpper"]
            contourRGB = self.vars["foosmenRedContour"]
            rectangleRGB = self.vars["foosmenRedBox"]
        else:
            foosmenMask = self.vars["foosmenBLUEMask"]
            hsvLower = self.vars["foosmenBlueHSVLower"]
            hsvUpper = self.vars["foosmenBlueHSVUpper"]
            contourRGB = self.vars["foosmenBlueContour"]
            rectangleRGB = self.vars["foosmenBlueBox"]

        # Get mask and apply mask to image
        # Create mask containing "only" the areas with the rods for RED/BLUE foosmen
        origImg = self.frame.copy()
        maskedImg = cv2.bitwise_and(origImg, foosmenMask)

        # Convert to HSV color range
        blurred = cv2.GaussianBlur(maskedImg, (11, 11), 0)
        hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

        # Create color mask for foosmen and perform erosions and dilation to remove small blobs in mask
        mask = cv2.inRange(hsv, hsvLower, hsvUpper)
        mask = cv2.erode(mask, None, iterations=4)
        mask = cv2.dilate(mask, None, iterations=4)

        # Detect foosmen using contours
        players = self._getContours(mask)

        # Overlay contour and rectangle over each player
        self.playersImg = np.zeros((self.vars["height"], self.vars["width"], 3), dtype="uint8")
        for i in players:

            # Get coordinates of bounding rectangle and draw rectangle on output image
            x, y, w, h = cv2.boundingRect(i)
            cv2.drawContours(self.playersImg, [i], -1, contourRGB, -1)
            cv2.rectangle(self.playersImg, (x, y), (x + w, y + h), rectangleRGB, 2)

        if self.debug:
            self.log("[DEBUG] Detect players end")


    # Detect ArUco markers and transform perspective
    # This effectively crops the frame to just show the foosball table
    def findTable(self):
        if self.debug:
            self.log("[DEBUG] Detect table begin")

        origImg = self.rawFrame.copy()

        # Detect markers
        # `corners` is the list of corners returned in clockwise order: top left, top right, bottom right, bottom left
        # `ids` is a list of marker IDs of each of the detected markers
        #gray = cv2.cvtColor(origImg, cv2.COLOR_BGR2GRAY)
        #arucoDict = aruco.Dictionary_get(aruco.DICT_4X4_50)
        #arucoParameters =  aruco.DetectorParameters_create()
        #corners, ids, rejectedImgPoints = aruco.detectMarkers(gray, arucoDict, parameters=arucoParameters)
        #print(ids)

        # Display detected markers
        #if ids is not None:
            #self.log("[INFO] ArUco markers detected:")
            #self.log(ids)
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
            #if self.debug:
                #self.log("[DEBUG] Table boundaries (tL, tR, bR, bL): {}".format(self.tableCoords))
            #for i in range(0, len(ids)):
                #id = str(ids[i][0])

                #marker = np.squeeze(corners[i])

                #x0, y0 = marker[0]
                #x2, y2 = marker[2]
                #x = int((x0 + x2)/2)
                #y = int((y0 + y2)/2)

                #result.add((id, x, y))
        #else:
            #self.log("[INFO] No ArUco markers detected, use defaults")

        # Apply projective transformation (also known as "perspective transformation" or "homography") to the
        # original image. This type of transformation was chosen because it preserves straight lines.
        # To do this, we first compute the transformational matrix (M) and then apply it to the original image.
        # The resulting frame will have an aspect ratio identical to the size (in pixels) of the foosball playing field
        self.origCoords = np.array(self.tableCoords, dtype="float32")
        finalCoords = np.array([(0, 0), (self.vars['width'] - 1, 0), (self.vars['width'] - 1, self.vars['height'] - 1), (0, self.vars['height'] - 1)], dtype="float32")
        M = cv2.getPerspectiveTransform(self.origCoords, finalCoords)
        self.frame = cv2.warpPerspective(origImg, M, (self.vars['width'], self.vars['height']))

        if self.debug:
            self.log("[DEBUG] Detect table end")

        return self.frame


    # Determine which foosmen row is closest to the foosball
    # Rows 0, 1, 3, and 5 are controlled by the automated player
    def getClosestRow(self, projectedX = None):
        if self.debug:
            self.log("[DEBUG] Get Closest Row begin")

        # If no projected coordinate exists, set to last row
        if projectedX is None:
            self.getClosestRow = 7

        # Otherwise, loop through all rows to determine which is closest to the projected X coordinate
        else:
            self.closestRow = 7
            min = self.vars["width"]

            # Loop through foosball rows and determine which is closest to X-coordinate of the foosball's current position
            for row in range(len(self.vars["rowPosition"])):
                if abs(self.vars["rowPosition"][row] - projectedX) < min:
                    min = abs(self.vars["rowPosition"][row] - projectedX)
                    self.closestRow = row

        if self.debug:
            self.log("[DEBUG] Get Closest Row end")

        return self.closestRow


    # Get contours
    def _getContours(self, mask):

        # Detect object using contours
        # We are using OpenCV 4.x, so extract contours from the 1st parameter
        contours, hierarchy = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        return contours


    # Determine which WALL the foosball will hit next
    # We use linear interpolation, along with the latest coordinates, to calculate this
    def _getIntersectingWallPosition(self):

        # Calculate latest two coordinates for interpolation
        x2 = self.ballPositions[-1:][0][0]
        y2 = self.ballPositions[-1:][0][1]
        x1 = x2 - self.deltaX
        y1 = y2 - self.deltaY

        # The ball is heading towards our goal (LEFT)
        if self.deltaX < 0:
            wallX = 0
            wallY = self._interpolate(wallX, x2, y2, x1, y1)
            if wallY >= 0 and wallY <= self.vars["height"]:
                self.projectedWallPosition = [wallX, int(wallY)]
                if self.debug:
                    self.log("[DEBUG] Projected wall intersection is LEFT wall at coordinates: {}".format(self.projectedWallPosition))

        # The ball is heading towards our opponent's goal (RIGHT)
        elif self.deltaX > 0:
            wallX = self.vars["width"]
            wallY = self._interpolate(wallX, x2, y2, x1, y1)
            if wallY >= 0 and wallY <= self.vars["height"]:
                self.projectedWallPosition = [wallX, int(wallY)]
                if self.debug:
                    self.log("[DEBUG] Projected wall intersection is RIGHT wall at coordinates: {}".format(self.projectedWallPosition))

        # The ball is heading towards our side (DOWN)
        elif self.deltaY < 0:
            wallY = 0
            wallX = self._interpolate(wallY, y2, x2, y1, x1)
            if wallX >= 0 and wallX <= self.vars["width"]:
                self.projectedWallPosition = [wallX, int(wallY)]
                if self.debug:
                    self.log("[DEBUG] Projected wall intersection is BOTTOM wall at coordinates: {}".format(self.projectedWallPosition))

        # The ball is heading towards our opponent's side (UP)
        elif self.deltaY > 0:
            wallY = self.vars["height"]
            wallX = self._interpolate(wallY, y2, x2, y1, x1)
            if wallX >= 0 and wallX <= self.vars["width"]:
                self.projectedWallPosition = [wallX, int(wallY)]
                if self.debug:
                    self.log("[DEBUG] Projected wall intersection is TOP wall at coordinates: {}".format(self.projectedWallPosition))

        # Something went wrong
        else:
            self.projectedWallPosition = None
            self.log("[ERROR] Could not identify projected WALL coordinates")


    # Get mask for RED or BLUE players based on foosmenRows array
    def _getMaskForPlayers(self, foosmenRows):
        if self.debug:
            self.log("[DEBUG] Get Mask for Mode begin")

        mask = np.zeros((self.vars["height"], self.vars["width"], 3), dtype="uint8")

        # Add "whitelabel" mask for each rod containing foosmen with matching color
        for rod in foosmenRows:
            # Create "vertical strips" that are 2 x "foosmenHeight" pixels wide, spanning entire frame (0 to yMax height)
            cv2.rectangle(mask, (int(rod - self.vars["foosmenHeight"]), 0), (int(rod + self.vars["foosmenHeight"]), self.vars["height"]), (255, 255, 255), -1)
        mask = cv2.resize(mask, mask.shape[1::-1])

        if self.debug:
            self.log("[DEBUG] Get Mask for Mode end")

        return mask


    # Get projected X coordinate of ball, if it exists
    def getProjectedX(self):
        if self.projectedPosition is None:
            self.projectedX = None
        else:
            self.projectedX = self.projectedPosition[0]

        return self.projectedX


    # We use linear interpolation between two points (x1, y1) and (x2, y2)
    # to determine the future intersection point (xi, yi) for a fixed xi
    def _interpolate(self, xi, x2, y2, x1, y1):
        return (xi - x1) * (y2 - y1) / (x2 - x1) + y1


    # Determine if the ball position of the foosball is currently known
    # This returns true, even in the case of ball occlusion
    def isKnownBallPosition(self):
        return self.foosballPosition is not None


    # Print output message to console
    def log(self, msg):
        print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"), msg)


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
