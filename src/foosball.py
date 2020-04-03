import cv2
import datetime
import imutils
import numpy as np
import time


class foosball:

    # Initialize table
    def __init__(self, debug=False, usePiCamera=False, videoFile=None, outputFile=None):

        # Pre-calculate dimensions for table, foosmen, foosball, rods, etc
        # Store these for faster lookup, to reduce the amount of overhead required while playing
        self.dim = {

            # Foosball Table
            'table': {
                'xMax': 116.8,  # Table length
                'yMax': 68,     # Table width
                'margin': 1.75, # Minimum distance between foosmen and the wall
                'rows': np.array(), # X coordinate of each foosball rod (8 total)
            },

            # Goal
            'goal': {
                'width': 18.5,
            },

            # Motors
            'motors': {
                'limits': np.array(),
            },

            # Foosmen
            'foosmenWidth': 2.5,    # Foosmen width in "y" direction
            'foosmen': np.array(
                {'limits': np.array(), 'players': 3, 'spacing': 18.3},  # Goalie
                {'limits': np.array(), 'players': 2, 'spacing': 24.5},  # Defense
                {'limits': np.array(), 'players': 5, 'spacing': 12},    # Midfield
                {'limits': np.array(), 'players': 3, 'spacing': 18.5},  # Offense
            ),

            # Ball
            'ball': {
                'width': 3.5,  # Foosball width (in "y" direction)
            },
        }

        # Motor Limits
        # This is the maximum position for the motors in each rod
        self.dim['motors']['limits'].append(self.dim.table.yMax - (self.dim.foosmen[0].players - 1) * self.dim.foosmen[0].spacing - 2 * self.dim.table.margin)
        self.dim['motors']['limits'].append(self.dim.table.yMax - (self.dim.foosmen[1].players - 1) * self.dim.foosmen[1].spacing - 2 * self.dim.table.margin)
        self.dim['motors']['limits'].append(self.dim.table.yMax - (self.dim.foosmen[2].players - 1) * self.dim.foosmen[2].spacing - 2 * self.dim.table.margin)
        self.dim['motors']['limits'].append(self.dim.table.yMax - (self.dim.foosmen[3].players - 1) * self.dim.foosmen[3].spacing - 2 * self.dim.table.margin)

        # Maximum Position of Foosmen
        # Row 1
        self.dim['foosmen'][0]['limits'].append([self.dim.table.margin + 0 * self.dim.foosmen[0].spacing, self.dim.table.yMax - (self.dim.table.margin + 2 * self.dim.foosmen[0].spacing)])
        self.dim['foosmen'][0]['limits'].append([self.dim.table.margin + 1 * self.dim.foosmen[0].spacing, self.dim.table.yMax - (self.dim.table.margin + 1 * self.dim.foosmen[0].spacing)])
        self.dim['foosmen'][0]['limits'].append([self.dim.table.margin + 2 * self.dim.foosmen[0].spacing, self.dim.table.yMax - (self.dim.table.margin + 0 * self.dim.foosmen[0].spacing)])
        # Row 2
        self.dim['foosmen'][1]['limits'].append([self.dim.table.margin + 0 * self.dim.foosmen[1].spacing, self.dim.table.yMax - (self.dim.table.margin + 2 * self.dim.foosmen[1].spacing)])
        self.dim['foosmen'][1]['limits'].append([self.dim.table.margin + 1 * self.dim.foosmen[1].spacing, self.dim.table.yMax - (self.dim.table.margin + 1 * self.dim.foosmen[1].spacing)])
        # Row 3
        self.dim['foosmen'][2]['limits'].append([self.dim.table.margin + 0 * self.dim.foosmen[2].spacing, self.dim.table.yMax - (self.dim.table.margin + 4 * self.dim.foosmen[2].spacing)])
        self.dim['foosmen'][2]['limits'].append([self.dim.table.margin + 1 * self.dim.foosmen[2].spacing, self.dim.table.yMax - (self.dim.table.margin + 3 * self.dim.foosmen[2].spacing)])
        self.dim['foosmen'][2]['limits'].append([self.dim.table.margin + 2 * self.dim.foosmen[2].spacing, self.dim.table.yMax - (self.dim.table.margin + 2 * self.dim.foosmen[2].spacing)])
        self.dim['foosmen'][2]['limits'].append([self.dim.table.margin + 3 * self.dim.foosmen[2].spacing, self.dim.table.yMax - (self.dim.table.margin + 1 * self.dim.foosmen[2].spacing)])
        self.dim['foosmen'][2]['limits'].append([self.dim.table.margin + 4 * self.dim.foosmen[2].spacing, self.dim.table.yMax - (self.dim.table.margin + 0 * self.dim.foosmen[2].spacing)])
        # Row 4
        self.dim['foosmen'][3]['limits'].append([self.dim.table.margin + 0 * self.dim.foosmen[3].spacing, self.dim.table.yMax - (self.dim.table.margin + 2 * self.dim.foosmen[3].spacing)])
        self.dim['foosmen'][3]['limits'].append([self.dim.table.margin + 1 * self.dim.foosmen[3].spacing, self.dim.table.yMax - (self.dim.table.margin + 1 * self.dim.foosmen[3].spacing)])
        self.dim['foosmen'][3]['limits'].append([self.dim.table.margin + 2 * self.dim.foosmen[3].spacing, self.dim.table.yMax - (self.dim.table.margin + 0 * self.dim.foosmen[3].spacing)])

        # Goal Posts
        self.dim['goal']['limits'].append((self.dim.table.yMax - self.dim.goal) / 2, (self.dim.table.yMax - self.dim.goal) / 2 + self.dim.goal)

        # Row Positions ("x" coordinates)
        self.dim.table['rows'].append(1 * self.dim.table.xMax / 16) # Row 1
        self.dim.table['rows'].append(3 * self.dim.table.xMax / 16) # Row 2
        self.dim.table['rows'].append(5 * self.dim.table.xMax / 16) # Row 3
        self.dim.table['rows'].append(7 * self.dim.table.xMax / 16) # Row 4
        self.dim.table['rows'].append(9 * self.dim.table.xMax / 16) # Row 5
        self.dim.table['rows'].append(11 * self.dim.table.xMax / 16) # Row 6
        self.dim.table['rows'].append(13 * self.dim.table.xMax / 16) # Row 7
        self.dim.table['rows'].append(15 * self.dim.table.xMax / 16) # Row 8

        # Tracking Methods
        self.trackingMethods = ['Simple', 'Defense', 'Trajectory']


        # Initialize motors and all I/O ports
        # This includes calibration of the motors for linear and rotational motion
        self.motors = None

        # Initialize goal interrupt service routine (ISR)
        # If a goal is detected, this helps us keep track of score and reset for the next ball drop
        self.goalDetect = False

        # Initialize camera or video feed
        self.debug = debug
        self.usePiCamera = usePiCamera
        self.videoFile = videoFile
        self.outputFile = outputFile
        self.writer = None

        # Initialize score to 0-0
        self.score = (0, 0)

        if self.debug:
            self.out("Initialize Table")

        # Variable to determine if a game is current in progress or not
        # This can be toggled at any time to STOP or PAUSE play
        self.playing = False

        return self


    # Start game
    def start(self):
        if self.debug:
            self.out("Foosball Start function called")

        #self.playing = True
        return self


    # Play game
    def play():

        self.playing = True

        # Break if "playing" variable is not set or is false
        while self.playing:

            # Detect the position of the foosball
            self.position = None

            # Keep process if foosball was not detected
            if self.position is None:
                if self.debug:
                    self.out("Foosball position was not detected")
                continue

            # Determine the tracking method to use
            self.trackingMethod = "simple"

            # Calculate the foosmen position based on the tracking method

            # Apply takeover to determine in each row should track the ball

            # Calculate the motor positions required to put the tracking foosmen in the desired location

            # Move the motors based on the desired position


    # Linear interpolation between two points (x1, y1) and (x2, y2) and evaluates
    # the function at point xi
    def interpolate(xi, x2, y2, x1, y1):
        return (xi - x1) * (y2 - y1) / (x2 - x1) + y1


    # Retrieves the next frame from the camera or video feed
    def nextFrame():
        if self.debug:
            self.out("Next Frame function called")


    # image from the camera or video feed, performs object recognition,
    # and converts this information into the coordinate of the foosball
    def detectFoosball():
        if self.debug:
            self.out("Detect Foosball function called")


    # This function reads the
    def detectPlayers():
        if self.debug:
            self.out("Detect RED and BLUE players")


    def detectScore():
        if self.debug:
            self.out("Check to see if a score occurred")


    def detectUserInput():
        if self.debug:
            self.out("Check for user interrupt")
        return cv2.waitKey(1) & 0xFF == ord("q")


    # Function to update video display
    def update(images, ballLocation, ballRadius, ballDistance, ballDirection, ballSpeed):

    	# Grab dimensions of first image
    	(h, w) = images[0].shape[:2]

    	# Build multiview display
    	padding = 8
    	mvHeight = (h * 2) + (20 * 3) + (padding * 2)
    	mvWidth = w * 2 + padding
    	output = np.zeros((mvHeight, mvWidth, 3), dtype="uint8")

    	# Top Left
    	cv2.putText(output, "Original", (280, 15), cv2.FONT_HERSHEY_PLAIN, 1, (255, 255, 255), 1)
    	output[20:h+20, 0:w] = images[0]

    	# Top Right
    	cv2.putText(output, "Grayscale", (880, 15), cv2.FONT_HERSHEY_PLAIN, 1, (255, 255, 255), 1)
    	output[20:h+20, w+8:w*2+8] = images[1]

    	# Bottom Left
    	cv2.putText(output, "Mask", (280, 20+h+3+15), cv2.FONT_HERSHEY_PLAIN, 1, (255, 255, 255), 1)
    	output[h+3+20+20:h*2+3+20+20, 0:w] = images[2]

    	# Bottom Right
    	cv2.putText(output, "Output", (880, 20+h+3+15), cv2.FONT_HERSHEY_PLAIN, 1, (255, 255, 255), 1)
    	output[h+3+20+20:h*2+3+20+20, w+8:w*2+8] = images[3]

    	# Bottom
    	cDisplay = ("{}".format(ballLocation)) if ballLocation is not None else "-"
    	rDisplay = ("%2.1f" % ballRadius) if ballRadius is not None else "-"
    	dDisplay = ("%2.1f" % ballDistance) if ballDistance is not None else "-"
    	aDisplay = ("%2.1f" % ballDirection) if ballDirection is not None else "-"
    	vDisplay = "-"
    	cv2.putText(output, "Center: %s" % cDisplay, (90, mvHeight - 5), cv2.FONT_HERSHEY_PLAIN, 1, (255, 255, 255), 1)
    	cv2.putText(output, "Radius: %s" % rDisplay, (290, mvHeight - 5), cv2.FONT_HERSHEY_PLAIN, 1, (255, 255, 255), 1)
    	cv2.putText(output, "Distance: %s" % dDisplay, (420, mvHeight - 5), cv2.FONT_HERSHEY_PLAIN, 1, (255, 255, 255), 1)
    	cv2.putText(output, "Direction: %s" % aDisplay, (620, mvHeight - 5), cv2.FONT_HERSHEY_PLAIN, 1, (255, 255, 255), 1)
    	cv2.putText(output, "Velocity: %s" % vDisplay, (820, mvHeight - 5), cv2.FONT_HERSHEY_PLAIN, 1, (255, 255, 255), 1)

    	return output


    def out(msg):
        print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"), str)


    def toggleDebugMode():
        self.debug = not self.debug
        self.out("Debug Mode is now:", self.debug)
