from adafruit_motorkit import MotorKit
import cv2
import datetime
import imutils
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
            'xMax': 116.8,        # Table length
            'yMax': 68,           # Table width
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

        # Initialize score to 0-0
        self.score = (0, 0)

        return self


    # Check if a goal occurred
    def checkForGoal(self):
        if self.debug:
            self.log("Check to see if a score occurred")


    # Take current image, perform object recognition,
    # and convert this information into the coordinate of the foosball
    def detectBall(self):
        if self.debug:
            self.log("Detect Foosball function called")


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


    def getMotor(self, i):
        if self.debug:
            self.log("Get Motor [{}]".format(i))

        return self.motors[i]


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


    # Transform perspective based on 4 input points (coords)
    def perspectiveTransform(self, coords):
        origImg = self.rawFrame.copy()

        # Grab image dimensions and apply perspective transform
        # Apply the four point tranform to obtain a "birds eye view" of image
        (h, w) = origImg.shape[:2]
        self.frame = perspective.four_point_transform(origImg, coords)

        # Resulting frame should have an aspect ratio around 510px x 297px
        return self.frame


    # Play game
    def play(self):

        # Start game
        self.gameIsActive = True
        self.ballIsInPlay = False

        # Break if "playing" variable is not set or is false
        while self.gameIsActive:

            # Detect the position of the foosball
            self.position = None

            # Keep process if foosball was not detected
            if self.position is None:
                if self.debug:
                    self.log("Foosball position was not detected")
                continue

            # Determine the tracking method to use
            self.trackingMethod = self.determineTrackingMethod()

            # Calculate the foosmen position based on the tracking method

            # Apply takeover to determine in each row should track the ball
            self.foosmenTakeover()

            # Calculate the motor positions required to put the tracking foosmen in the desired location
            self.determineMotorMovement()

            # Move the motors based on the desired position
            self.moveMotors()


    # Rotate and crop
    #def rotateAndCrop(self):

        # grab the rotation matrix (apply the negative of the angle to rotate clockwise)
        #M = cv2.getRotationMatrix2D((cX, cY), 1, 1.0)
        # Rotate and crop image
        #rotatedImg = cv2.warpAffine(image, M, (w, h))
        #croppedImg = rotatedImg[125:h-62, 50:w-65]
        #croppedImg = rotatedImg[100:h - 50, 25: w - 25]

        #self.frame = croppedImg

        #return self.frame


    # Set next frame
    def setRawFrame(self, frame):
        if self.debug:
            self.log("Set next frame")

        self.rawFrame = frame


    # Function to update video display
    def updateDisplay(self, images, ballLocation, ballRadius, ballDistance, ballDirection, ballSpeed):

        if self.debug:
            self.log("Update multi view display")

        # Grab dimensions of first image
        (h, w) = images[0].shape[:2]

        # Build multiview display
        padW = 8
        padH = 20
        mvHeight = (h * 2) + (padH * 3) + (padW * 2)
        mvWidth = w * 2 + padW
        output = np.zeros((mvHeight, mvWidth, 3), dtype="uint8")

        # Top Left
        cv2.putText(output, "Cropped", (w // 2 - 35, 15), cv2.FONT_HERSHEY_PLAIN, 1, (255, 255, 255), 1)
        output[padH:h+padH, 0:w] = images[0]

        # Top Right
        cv2.putText(output, "Grayscale", (w + w // 2 - 30, 15), cv2.FONT_HERSHEY_PLAIN, 1, (255, 255, 255), 1)
        output[padH:h+padH, w+padW:w*2+padW] = images[1]

        # Bottom Left
        cv2.putText(output, "Mask", (w // 2 - 35, 20+h+3+15), cv2.FONT_HERSHEY_PLAIN, 1, (255, 255, 255), 1)
        output[h+3+padH+padH:h*2+3+padH+padH, 0:w] = images[2]

        # Bottom Right
        cv2.putText(output, "Output", (w + w // 2 - 30, 20+h+3+15), cv2.FONT_HERSHEY_PLAIN, 1, (255, 255, 255), 1)
        output[h+3+padH+padH:h*2+3+padH+padH, w+padW:w*2+padW] = images[3]

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


    def toggleDebugMode(self):
        self.debug = not self.debug
        self.log("Debug Mode is now:", self.debug)
