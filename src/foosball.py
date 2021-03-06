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

        # Track console log in buffer to save processing time
        self.msgs = []

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

            # Output coordinates of frame
            'outputCoords': [(0, 0), (639, 0), (639, 359), (0, 359)],

            # Add additional spacing below picture for output display
            'outputWidth': 640,                     # Output width is the same as table width
            'outputHeight': 484,                    # Output height is 124px more than table height
            'outputFont': cv2.FONT_HERSHEY_PLAIN,   # Font for text on output image

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
            'foosballHSVLower': (19, 50, 50),       # Foosball lower bound (HSV)
            'foosballHSVUpper': (26, 200, 200),     # Foosball upper bound (HSV)
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
            #'rowPosition': [43.19, 122.28, 201.37, 280.46, 359.55, 438.64, 517.73, 596.82],
            'rowPosition': [29, 114, 197, 280, 360, 443, 526, 611],
            'foosmenBLUE': [0, 1, 3, 5],
            'foosmenRED': [2, 4, 6, 7],

            # The foosmen are centered on each rod, but each rod (row) has a different number of men
            # There are 13 total foosmen, each with a unique ID from left to right and top to bottom
            # Each foosmen kicks the ball with feet that measure 1" in width
            'foosmenHeight': 42,                    # Foosmen height (how far they "span" in either direction)

            # RED players
            'foosmenRedHSV1Lower': (0, 0, 0),       # Foosmen lower bound (HSV)
            'foosmenRedHSV1Upper': (10, 255, 255),  # Foosmen upper bound (HSV)
            'foosmenRedHSV2Lower': (170, 0, 0),     # Foosmen lower bound (HSV)
            'foosmenRedHSV2Upper': (180, 255, 255), # Foosmen upper bound (HSV)
            'foosmenRedContour': (100, 100, 255),   # Foosmen contour highlight color
            'foosmenRedBox': (0, 0, 255),           # Foosmen bounding box color

            # BLUE players
            'foosmenBlueHSVLower': (85, 0, 0),      # Foosmen lower bound (HSV)
            'foosmenBlueHSVUpper': (110, 255, 255), # Foosmen upper bound (HSV)
            'foosmenBlueContour': (255, 100, 100),  # Foosmen contour highlight color
            'foosmenBlueBox': (255, 0, 0)           # Foosmen bounding box color
        }

        # Variable to determine if a game is currently in progress or not
        # This can be toggled at any time to STOP or PAUSE play
        self.gameIsActive = False
        self.ballIsInPlay = False
        self.arucoDetected = False
        self.foosballDetected = False
        self.playersDetected = False

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
        tL = (58,118)
        tR = (544,130)
        bR = (544,409)
        bL = (43,395)
        self.tableCoords = [tL, tR, bR, bL]

        # Start game
        self.gameIsActive = True
        self.ballIsInPlay = False
        self.foosballDetected = False

        # History of foosball position/coordinates
        self.ballPositions = []
        self.lostBallFrames = 0
        self.foosballPosition = None
        self.projectedPosition = None
        #self.projectedWallPosition = None

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
            self.deltaX = int((self.ballPositions[-1:][0][0] - self.ballPositions[-2:][0][0]) / 1)
            self.deltaY = int((self.ballPositions[-1:][0][1] - self.ballPositions[-2:][0][1]) / 1)

        # Otherwise, calculate deltas based on last 3 known points
        else:
            self.deltaX = int((self.ballPositions[-1:][0][0] - self.ballPositions[-3:][0][0]) / 2)
            self.deltaY = int((self.ballPositions[-1:][0][1] - self.ballPositions[-3:][0][1]) / 2)

        # Ignore deltas unless there is "significant" movement
        if abs(self.deltaX) + abs(self.deltaY) < 2:
            if self.debug:
                self.log("[DEBUG] Ignore insignificant movement for projected positions")
            self.deltaX = 0
            self.deltaY = 0

        # Calculate which wall the ball will hit next, assuming it continues uninterrupted
        #self._getIntersectingWallPosition()

        # Calculate projected next coordinate
        self.projectedPosition = (self.ballPositions[-1:][0][0] + self.deltaX, self.ballPositions[-1:][0][1] + self.deltaY)

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
        out = np.zeros((self.vars["outputHeight"], self.vars["outputWidth"], 3), dtype="uint8")
        vPos = self.vars["height"] + 4

        # Output image
        out[0:self.vars["height"], 0:self.vars["width"]] = self.outputImg

        # Key metrics
        metrics = {
            "Elapsed": ("%5.2f s" % self.elapsedTime) if self.elapsedTime is not None else "-",
            #"In Play": self.ballIsInPlay,
            "Detect Markers": self.arucoDetected,
            "Detect Ball": self.foosballDetected,
            "Detect Players": self.playersDetected,
            #"Distance": ("%2.1f cm" % self.distance) if self.distance is not None else "-",
            "Velocity": ("%2.1f m/s" % self.velocity) if self.velocity is not None else "-",
            "FPS": ("%2.1f" % self.fps) if self.fps is not None else "-",
        }
        metricsRight = {
            "Score": self.score,
            "Current": ("{}".format(self.foosballPosition)) if self.foosballPosition is not None else "-",
            "Projected": ("{}".format(self.projectedPosition)) if self.projectedPosition is not None else "-",
            #"Wall": ("{}".format(self.projectedWallPosition)) if self.projectedWallPosition is not None else "-",
        }
        for key in metrics:
            vPos += 18
            cv2.putText(out, "%s: %s" % (key, metrics[key]), (10, int(vPos)), self.vars["outputFont"], 1, (255, 255, 255), 1)

        vPos = self.vars["height"] + 4

        for key in metricsRight:
            vPos += 18

            # get boundary of this text
            text = "%s: %s" % (key, metricsRight[key])
            textsize = cv2.getTextSize(text, self.vars["outputFont"], 1, 2)[0]

            # get coords based on boundary
            textX = self.vars["width"] - textsize[0] - 10

            # add text centered on image
            cv2.putText(out, text, (int(textX), int(vPos)), self.vars["outputFont"], 1, (255, 255, 255), 1)

        if self.debug:
            self.log("[DEBUG] Update display end")

        return out


    # Determine if a goal was scored or not
    def _checkForGoal(self):

        # An actual goal can only happen once
        if self.lostBallFrames > 1:
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

        origImg = self.frame.copy()

        # Convert to HSV color range
        self.blurred = cv2.GaussianBlur(origImg, (11, 11), 0)
        self.hsv = cv2.cvtColor(self.blurred, cv2.COLOR_BGR2HSV)

        # Create mask and perform morphological "opening" to remove small blobs in mask.
        # Opening erodes an image and then dilates the eroded image, using the same structuring
        # element for both operations. This is useful for removing small objects from an image
        # while preserving the shape and size of larger objects in the image.
        mask = cv2.inRange(self.hsv, self.vars["foosballHSVLower"], self.vars["foosballHSVUpper"])
        mask = cv2.erode(mask, None, iterations=2)
        mask = cv2.dilate(mask, None, iterations=2)

        #self.radius = None
        self.distance = None
        #self.degrees = None
        self.velocity = None

        # Find largest contour in mask
        cnts = self._getContours(mask)
        # Sort from largest to smallest
        #cnts = sorted(cnts, key=cv2.contourArea, reverse=True)
        #if self.debug:
            #self.log("[DEBUG] Contours found: {}".format(len(cnts)))

        if self.debug:
            self.log("[DEBUG] {} contour(s) found".format(len(cnts)))

        if len(cnts) > 0:

            # Draw all contours on output image
            for c in cnts:
                #perimeter = cv2.arcLength(c, True)
                #epsilon = 0.04 * perimeter
                #approx = cv2.approxPolyDP(c, epsilon, True)
                cv2.drawContours(self.outputImg, [c], -1, (30, 255, 255), -1)

            # Find largest contour and draw on output image with a different color
            c = max(cnts, key=cv2.contourArea)
            cv2.drawContours(self.outputImg, [c], -1, (60, 255, 255), -1)


            self.foosballDetected = True
            self.ballIsInPlay = True

            # compute the minimum enclosing circle and centroid
            #((x, y), self.radius) = cv2.minEnclosingCircle(c)
            M = cv2.moments(c)
            self.foosballPosition = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))

            # Add current position to the list of tracked points
            self._addCurrentPosition(self.foosballPosition)

            # Draw centroid
            #cv2.circle(self.outputImg, self.foosballPosition, 5, (0, 0, 255), -1)

            # Draw projected coordinates between current position and wall
            #if self.projectedWallPosition is not None:
                #cv2.line(self.outputImg, self.foosballPosition, self.projectedWallPosition, (255,0,0), 5)
                #self.log("[INFO] Intersecting wall coordinates: {}".format(self.projectedWallPosition))

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


    # Take current image, find goal using location detetction,
    # and overlay rectangular area on output image
    def findGoal(self):
        if self.debug:
            self.log("[DEBUG] Find Goal begin")

        # Goal boundaries
        tL = [self.vars["width"] - 10, self.vars["goalUpper"]]
        tR = [self.vars["width"] - 1, self.vars["goalUpper"]]
        bR = [self.vars["width"] - 1, self.vars["goalLower"]]
        bL = [self.vars["width"] - 10, self.vars["goalLower"]]
        pts = np.array([tL, tR, bR, bL], np.int32)
        pts = pts.reshape((-1, 1, 2))

        # Draw rectangle around goal on output frame
        self.outputImg = cv2.polylines(self.outputImg, [pts], True, (255, 255, 255), 8)

        if self.debug:
            self.log("[DEBUG] Find Goal end")


    # Take current image, perform object recognition,
    # and convert this information into the coordinates of the RED and BLUE players
    def findPlayers(self, mode, myPlayer = False):
        if self.debug:
            self.log("[DEBUG] Detect players begin")

        origImg = self.frame.copy()

        # Convert to HSV color range
        blurred = cv2.GaussianBlur(origImg, (11, 11), 0)
        hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

        # Set variables based on mode (RED or BLUE)
        self.foosmenDetected = False
        if mode == "RED":
            contourRGB = self.vars["foosmenRedContour"]
            rectangleRGB = self.vars["foosmenRedBox"]
            foosmenRodArray = self.vars["foosmenRED"]

            # Create color mask for foosmen and perform erosions and dilation to remove small blobs in mask
            mask1 = cv2.inRange(hsv, self.vars["foosmenRedHSV1Lower"], self.vars["foosmenRedHSV1Upper"])
            mask2 = cv2.inRange(hsv, self.vars["foosmenRedHSV2Lower"], self.vars["foosmenRedHSV2Upper"])
            mask = cv2.bitwise_or(mask1, mask2)
            mask = cv2.erode(mask, None, iterations=4)
            mask = cv2.dilate(mask, None, iterations=4)

        elif mode == "BLUE":
            contourRGB = self.vars["foosmenBlueContour"]
            rectangleRGB = self.vars["foosmenBlueBox"]
            foosmenRodArray = self.vars["foosmenBLUE"]

            # Create color mask for foosmen and perform erosions and dilation to remove small blobs in mask
            mask = cv2.inRange(hsv, self.vars["foosmenBlueHSVLower"], self.vars["foosmenBlueHSVUpper"])
            mask = cv2.erode(mask, None, iterations=4)
            mask = cv2.dilate(mask, None, iterations=4)

        else:
            self.log("[ERROR] Invalid `mode` in findPlayers() function")
            return

        # Draw line over each roosmen rod
        #for i, xPos in enumerate(foosmenRodArray):
        for row in foosmenRodArray:
            xPos = self.vars["rowPosition"][row]
            self.outputImg = cv2.line(self.outputImg, (xPos, 0), (xPos, self.vars["height"] - 1), (0, 255, 0), 2)

        # Detect foosmen using contours
        players = self._getContours(mask)

        # Loop through players to filter out false positives
        detectedPlayers = []
        for i in players:

            # Get coordinates of bounding rectangle
            x, y, w, h = cv2.boundingRect(i)

            # Draw rectangle on output image
            cv2.drawContours(self.outputImg, [i], -1, contourRGB, -1)
            cv2.rectangle(self.outputImg, (x, y), (x + w, y + h), rectangleRGB, 2)

            # Filter contours that are adjacent to the top or bottom of the table
            # We do this by using `rowMargin`, which stores the height of the "bumpers" on each side of the foosmen rod
            if ((y < self.vars["rowMargin"]) | (y > (self.vars["height"] - self.vars["rowMargin"]))):
                continue

            # Filter contours with abnormal width (smaller than acceptable width)
            if (h < 10):
                continue

            # Normalize xPos based on foosball rod. We do this by looping through
            # each of the 4 foosmen rods and determining if this contour falls
            # within an acceptable range of one of them.
            #for row, xPos in enumerate(foosmenRodArray):
            for row in foosmenRodArray:
                xPos = self.vars["rowPosition"][row]

                # Ensure boundaries are within acceptable margins on either side of foosmen rod
                #if ((x < xPos) & (xPos < (x + w))):
                if ((x > (xPos - self.vars["foosmenHeight"] - 8)) & (x < xPos) & ((x + w) < (xPos + self.vars["foosmenHeight"] + 8)) & ((x + w) > xPos)):

                    # Add player to detectedPlayers array
                    # Normalize x-coordinate by using [xPos] instead of [x + (w / 2)]
                    playerPos = (xPos, y + (h / 2))
                    detectedPlayers.append([row, playerPos[0], playerPos[1]])

                    # Draw contour and rectangle over player
                    cv2.drawContours(self.outputImg, [i], -1, contourRGB, -1)
                    cv2.rectangle(self.outputImg, (x, y), (x + w, y + h), rectangleRGB, 2)

        # Sort by x-coordinate (column 1), then by y-coordinate (column 2)
        dp = np.array(detectedPlayers)
        dp = dp[dp[:,2].argsort(kind='mergesort')]
        dp = dp[dp[:,1].argsort(kind='mergesort')]

        # Loop through detected players
        if myPlayer:
            totPlayersRow0 = 0
            totPlayersRow1 = 0
            totPlayersRow3 = 0
            totPlayersRow5 = 0

            for i, p in enumerate(dp):
                if self.debug:
                    self.log("[DEBUG] Player {} detected in foosmen rod {} with center at ({}, {})".format(i, p[0], p[1], p[2]))

                if p[0] == 0:
                    totPlayersRow0 += 1
                elif p[0] == 1:
                    totPlayersRow1 += 1
                elif p[0] == 2:
                    totPlayersRow3 += 1
                elif p[0] == 3:
                    totPlayersRow5 += 1

                # Add text to "tag" each detected player, center in each player box
                text = "P%s" % (i + 1)
                textsize = cv2.getTextSize(text, self.vars["outputFont"], 1, 2)[0]
                textX = p[1] - (textsize[0] / 2)
                textY = p[2] + (textsize[1] / 2)
                cv2.putText(self.outputImg, text, (int(textX), int(textY)), self.vars["outputFont"], 1, (255, 255, 255), 1)

            # Check if all players are detected
            if self.debug:
                self.log("[INFO] Total players detected in foosmen rod {}: {}".format(0, totPlayersRow0))
                self.log("[INFO] Total players detected in foosmen rod {}: {}".format(1, totPlayersRow1))
                self.log("[INFO] Total players detected in foosmen rod {}: {}".format(3, totPlayersRow3))
                self.log("[INFO] Total players detected in foosmen rod {}: {}".format(5, totPlayersRow5))
            if ((totPlayersRow0 == 3) & (totPlayersRow1 == 2) & (totPlayersRow3 == 5) & (totPlayersRow5 == 3)):
                self.playersDetected = True
                self.log("[INFO] All 13 players detected")
            else:
                self.playersDetected = False
                self.log("[INFO] All 13 players NOT detected")

        # TODO: Take action based on ball position and detected players

        if self.debug:
            self.log("[DEBUG] Detect players end")


    # Detect ArUco markers and transform perspective
    # This effectively crops the frame to just show the foosball table
    def findTable(self):
        if self.debug:
            self.log("[DEBUG] Detect table begin")

        origImg = self.rawFrame.copy()

        self.arucoDetected = False


        # Detect ArUco markers
        # `corners` is the list of corners returned in clockwise order: top left, top right, bottom right, bottom left
        # `ids` is a list of marker IDs of each of the detected markers
        gray = cv2.cvtColor(origImg, cv2.COLOR_BGR2GRAY)
        arucoDict = aruco.Dictionary_get(aruco.DICT_4X4_50)
        arucoParameters =  aruco.DetectorParameters_create()
        corners, ids, rejectedImgPoints = aruco.detectMarkers(gray, arucoDict, parameters=arucoParameters)
        #print(ids)

        # Make sure we found at least one markerId
        if ids is not None:

            # Iterate through detected markers
            detectedMarkers = []
            for i in range(len(ids)):
                markerId = int(str(ids[i][0]))
                marker = np.squeeze(corners[i])
                x0, y0 = marker[0]
                #if self.debug:
                    #self.log("[DEBUG] MarkerId {} detected at ({}, {})".format(markerId, x0, y0))

                # Account for difference between marker position and corner of table
                #detectedMarkers.append([markerId, x0, y0])
                if markerId == 0:
                    #tL = (36,111)
                    #tL = (58,118)
                    detectedMarkers.append([markerId, x0 + 22, y0 + 7])
                elif markerId == 1:
                    #tR = (568,123)
                    #tR = (544,130)
                    detectedMarkers.append([markerId, x0 - 24, y0 + 7])
                elif markerId == 2:
                    #bR = (570,401)
                    #bR = (544,409)
                    detectedMarkers.append([markerId, x0 - 26, y0 + 8])
                elif markerId == 3:
                    #bL = (21,388)
                    #bL = (43,395)
                    detectedMarkers.append([markerId, x0 + 22, y0 + 7])

            # Sort by markerId (column 0)
            dm = np.array(detectedMarkers)
            dm = dm[dm[:,0].argsort(kind='mergesort')]

            if self.debug:
                self.log("[DEBUG] {} ArUco markers detected".format(len(dm)))
                for i, m in enumerate(dm):
                    self.log("[DEBUG] MarkerId {} detected at ({}, {})".format(m[0], m[1], m[2]))

            # Update coordinates if exactly 4 ArUco markers were found
            if len(dm) == 4:
                self.arucoDetected = True
                self.tableCoords = []
                for i, m in enumerate(dm):
                    self.tableCoords.append((m[1], m[2]))
                self.log("[INFO] 4 ArUco markers detected, update table coordinates")
                self.log("[INFO] ArUco marker coordinates: {}".format(self.tableCoords))

            else:
                if self.debug:
                    self.log("[DEBUG] ArUco markers detected but not 4 total")

        else:
            if self.debug:
                self.log("[DEBUG] No ArUco markers detected, use default table coordinates")


        # Apply projective transformation (also known as "perspective transformation" or "homography") to the
        # original image. This type of transformation was chosen because it preserves straight lines.
        # To do this, we first compute the transformational matrix (M) and then apply it to the original image.
        # The resulting frame will have an aspect ratio identical to the size (in pixels) of the foosball playing field
        origCoords = np.array(self.tableCoords, dtype="float32")
        finalCoords = np.array(self.vars['outputCoords'], dtype="float32")
        M = cv2.getPerspectiveTransform(origCoords, finalCoords)
        self.frame = cv2.warpPerspective(origImg, M, (self.vars['width'], self.vars['height']))

        # Save output frame, to be used later for overlays and output display
        self.outputImg = self.frame.copy()

        if self.debug:
            self.log("[DEBUG] Detect table end")

        return self.frame


    # Get contours
    def _getContours(self, mask):

        # Detect object using contours
        # We are using OpenCV 4.x, so extract contours from the 1st parameter
        contours, hierarchy = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        return contours


    # # Determine intersecting y-coordinate based on x-coordinate
    # def getIntersectingYPos(self, xPos):
    #
    #     # Calculate latest two coordinates for interpolation
    #     x2 = self.ballPositions[-1:][0][0]
    #     y2 = self.ballPositions[-1:][0][1]
    #     x1 = x2 - self.deltaX
    #     y1 = y2 - self.deltaY
    #
    #     yPos = self._interpolate(xPos, x2, y2, x1, y1)
    #
    #     # Intersecting yPos is out of bounds
    #     while yPos < 0 or yPos > self.vars["height"]:
    #         if yPos > self.vars["height"]:
    #             yPos -= 2 * self.vars["height"]
    #         yPos = abs(yPos)
    #
    #     return int(yPos)
    #
    #
    # # Determine which WALL the foosball will hit next
    # # We use linear interpolation, along with the latest coordinates, to calculate this
    # def _getIntersectingWallPosition(self):
    #
    #     # Calculate latest two coordinates for interpolation
    #     x2 = self.ballPositions[-1:][0][0]
    #     y2 = self.ballPositions[-1:][0][1]
    #     x1 = x2 - self.deltaX
    #     y1 = y2 - self.deltaY
    #
    #     # The ball is heading towards our goal (LEFT)
    #     if self.deltaX < 0:
    #         wallX = 0
    #         wallY = self._interpolate(wallX, x2, y2, x1, y1)
    #         if wallY >= 0 and wallY <= self.vars["height"]:
    #             self.projectedWallPosition = (wallX, int(wallY))
    #             if self.debug:
    #                 self.log("[DEBUG] Projected wall intersection is LEFT wall at coordinates: {}".format(self.projectedWallPosition))
    #
    #     # The ball is heading towards our opponent's goal (RIGHT)
    #     elif self.deltaX > 0:
    #         wallX = self.vars["width"]
    #         wallY = self._interpolate(wallX, x2, y2, x1, y1)
    #         if wallY >= 0 and wallY <= self.vars["height"]:
    #             self.projectedWallPosition = (wallX, int(wallY))
    #             if self.debug:
    #                 self.log("[DEBUG] Projected wall intersection is RIGHT wall at coordinates: {}".format(self.projectedWallPosition))
    #
    #     # The ball is heading towards our side (DOWN)
    #     elif self.deltaY < 0:
    #         wallY = 0
    #         wallX = self._interpolate(wallY, y2, x2, y1, x1)
    #         if wallX >= 0 and wallX <= self.vars["width"]:
    #             self.projectedWallPosition = (int(wallX), wallY)
    #             if self.debug:
    #                 self.log("[DEBUG] Projected wall intersection is BOTTOM wall at coordinates: {}".format(self.projectedWallPosition))
    #
    #     # The ball is heading towards our opponent's side (UP)
    #     elif self.deltaY > 0:
    #         wallY = self.vars["height"]
    #         wallX = self._interpolate(wallY, y2, x2, y1, x1)
    #         if wallX >= 0 and wallX <= self.vars["width"]:
    #             self.projectedWallPosition = (int(wallX), wallY)
    #             if self.debug:
    #                 self.log("[DEBUG] Projected wall intersection is TOP wall at coordinates: {}".format(self.projectedWallPosition))
    #
    #     # The ball is not moving
    #     else:
    #         self.projectedWallPosition = None
    #         if self.debug:
    #             self.log("[DEBUG] No projected wall intersection, the ball is not currently moving")
    #
    #
    # # We use linear interpolation between two points (x1, y1) and (x2, y2)
    # # to determine the future intersection point (xi, yi) for a fixed xi
    # def _interpolate(self, xi, x2, y2, x1, y1):
    #     return (xi - x1) * (y2 - y1) / (x2 - x1) + y1


    # Print output message to console
    def log(self, msg, flush=False):
        self.msgs.append(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f") + " " + msg)
        if flush:
            print("\n".join(self.msgs))
            self.msgs = []


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


    # # Show trailing list of tracked points
    # def _updateTrackedPoints(self):
    #
    #     # Add latest point to list of tracked points
    #     self.pts.appendleft(self.foosballPosition)
    #
    #     # loop over the set of tracked points
    #     for i in range(1, len(self.pts)):
    #
    #     	# if either of the tracked points are None, ignore them
    #     	if self.pts[i - 1] is None or self.pts[i] is None:
    #     		continue
    #
    #     	# otherwise, compute the thickness of the line and draw the connecting lines
    #     	thickness = int(np.sqrt(30 / float(i + 1)) * 2.5)
    #     	cv2.line(self., self.pts[i - 1], self.pts[i], (0, 0, 255), thickness)
