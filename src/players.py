#########################
# Automated Foosball    #
#########################

# This class handles all of the foosmen
# Each row of foosmen has two motors, one for linear motion and one for rotational motion
# https://learn.adafruit.com/adafruit-dc-and-stepper-motor-hat-for-raspberry-pi/using-stepper-motors

# import the necessary packages
from adafruit_motor import stepper
from adafruit_motorkit import MotorKit
import datetime


class Foosmen:

    # Initialize foosmen row
    def __init__(self, id, numPlayers, playerSpacing, rowLength, playerWidth):

        # The ID of each foosmen row goes from left to right (0-7)
        self.id = id

        # The maximum position of each foosmen row
        self.maxPosition = rowLength

        # The current position is used for linear motion
        # 0 means the foosmen row is all the way towards the side with the motors
        self.position = 0

        # The current angle is used for rotational motion
        # 0 degrees means the players are vertical and facing the goal
        # +90 degrees means the players are horizontal and facing upwards
        # -90 degrees means the players are horizontal and facing downwards
        self.angle = 0

        # The number of foosmen on each row
        self.players = numPlayers

        # The number of pixels between two players on each row
        self.playerSpacing = playerSpacing

        # The width of each player, in pixels
        self.playerWidth = playerWidth

        # Each row of foosmen can operate in an "offensive" or "defensive" mode
        # Initiate to "defensive" until the ball position is known or changes
        self.mode = "DEFENSE"

        # The number of steps per pixel, used for linear motion
        self.pixelsPerStep = 1

        # The number of steps per revolution (360 degrees), used for rotational motion
        self.stepsPerRevolution = 200


    # Initialize motors and warm up
    def start(self):

        ##########################################################################
        # This section initializes the linear and rotational motors              #
        ##########################################################################

        # Each board in the stack must be assigned a unique address. This is done
        # with the address jumpers on the left side of the board. The I2C base
        # address for each board is 0x60. The binary address that you program
        # with the address jumpers is added to the base I2C address.

        # Initialize the 1st hat on the default address (0x60)
        # Board 0: Address = 0x60 Offset = binary 0000 (no jumpers required)
        if self.id == 0:
            motorAddr = 0x60

        # Initialize the 2nd hat on the default address (0x61)
        # Board 1: Address = 0x61 Offset = binary 0001 (bridge A0)
        elif self.id == 1:
            motorAddr = 0x61

        # Initialize the 3rd hat on the default address (0x63)
        # Board 2: Address = 0x62 Offset = binary 0010 (bridge A1, the one above A0)
        elif self.id == 3:
            motorAddr = 0x62

        # Initialize the 4th hat on the default address (0x67)
        # Board 4: Address = 0x64 Offset = binary 0100 (bridge A2, middle jumper)
        elif self.id == 5:
            motorAddr = 0x64

        else:
            self.log("[ERROR] Could not initialize motors")
            return


        # Stepper motors are available as stepper1 and stepper2
        # stepper1 is made up of the M1 and M2 terminals and used for linear motion
        # stepper2 is made up of the M3 and M4 terminals and used for rotational motion
        #self.motors = MotorKit(address=motorAddr)
        self.motors = None

        # Release motors so they can spin freely
        #self.motors.stepper1.release()
        #self.motors.stepper2.release()

        # Warm up motors
        self.log("[INFO] Warm up linear motors")
        #for i in range(25):
            #self.motors.stepper1.onestep(direction=stepper.FORWARD, style=stepper.SINGLE)
        #for i in range(25):
            #self.motors.stepper1.onestep(direction=stepper.BACKWARD, style=stepper.SINGLE)

        self.log("[INFO] Warm up rotational motors")
        #for i in range(50):
            #self.motors.stepper2.onestep(direction=stepper.FORWARD, style=stepper.SINGLE)
        #for i in range(100):
            #self.motors.stepper2.onestep(direction=stepper.BACKWARD, style=stepper.SINGLE)
        #for i in range(50):
            #self.motors.stepper2.onestep(direction=stepper.FORWARD, style=stepper.SINGLE)

        return self


    # Move linear motor one step BACKWARD
    def moveBackward(self):

        # Make sure next position is not out of bounds
        if self.position < self.pixelsPerStep:
            self.log("[ERROR] Cannot move foosmen row since it is past min position")
            return

        # Move backward one step
        self.position -= self.pixelsPerStep
        #self.motors.stepper1.onestep(direction=stepper.BACKWARD, style=stepper.SINGLE)
        self.log("[INFO] Move row {} one step BACKWARD, position is now: {}".format(self.id, self.position))


    # Move linear motor one step FORWARD
    def moveForward(self):

        # Make sure next position is not out of bounds
        if self.position + self.pixelsPerStep > self.maxPosition:
            self.log("[ERROR] Cannot move foosmen row since it is past max position")
            return

        # Move forward one step
        self.position += self.pixelsPerStep
        #self.motors.stepper1.onestep(direction=stepper.FORWARD, style=stepper.SINGLE)
        self.log("[INFO] Move row {} one step FORWARD, position is now: {}".format(self.id, self.position))


    # Move linear motor to get to specific position
    def moveTo(self, pos):

        # Make sure new position is different
        if pos == self.position:
            self.log("[ERROR] No need to move foosmen row {} since we are already at position: {}".format(self.id, pos))
            return

        # Make sure position is not out of bounds
        if pos > self.maxPosition:
            self.log("[ERROR] Cannot move foosmen row {} to position {} since it is past max position: {}".format(self.id, pos, self.maxPosition))
            return

        # Need to move forward
        if pos > self.position:
            numSteps = int((pos - self.position) * self.pixelsPerStep)
            self.log("[MOTOR] Move row {} {} steps FORWARD to position {}".format(self.id, numSteps, pos))
            for i in range(numSteps):
                self.moveForward()

        # Need to move backward
        else:
            numSteps = int((self.position - pos) * self.pixelsPerStep)
            self.log("[MOTOR] Move row {} {} steps BACKWARD to position {}".format(self.id, numSteps, pos))
            for i in range(numSteps):
                self.moveBackward()


    # Release motors so they can spin freely
    def releaseMotors(self):
        return
        #self.motors.stepper1.release()
        #self.motors.stepper2.release()


    # Move rotational motor one step BACKWARD
    def rotateBackward(self):

        # Make sure next angle is not out of bounds
        # Min angle is -90 degrees
        # There are 200 steps per revolution, so each step is 1.8 degrees
        if self.angle < -88.2:
            self.log("[ERROR] Cannot rotate foosmen row since it is past min angle")
            return

        # Move backward one step
        # There are 200 steps per revolution, so each step is 1.8 degrees
        self.angle -= (360 / self.stepsPerRevolution)
        #self.motors.stepper2.onestep(direction=stepper.BACKWARD, style=stepper.SINGLE)
        self.log("[INFO] Rotate row {} one step BACKWARD, angle is now: {}".format(self.id, self.angle))


    # Move rotational motor one step FORWARD
    def rotateForward(self):

        # Make sure next angle is not out of bounds
        # Max angle is +90 degrees
        # There are 200 steps per revolution, so each step is 1.8 degrees
        if self.angle > 88.2:
            self.log("[ERROR] Cannot rotate foosmen row since it is past max angle")
            return

        # Move forward one step
        # There are 200 steps per revolution, so each step is 1.8 degrees
        self.angle += (360 / self.stepsPerRevolution)
        #self.motors.stepper2.onestep(direction=stepper.FORWARD, style=stepper.SINGLE)
        self.log("[INFO] Rotate row {} one step FORWARD, angle is now: {}".format(self.id, self.angle))


    # Move rotational motor to get to specific angle
    def rotateTo(self, angle):

        # Make sure new angle is different
        if angle == self.angle:
            self.log("[ERROR] No need to rotate foosmen row {} since we are already at angle: {}".format(self.id, angle))
            return

        # Make sure angle is not out of bounds
        if angle < -90 or angle > 90:
            self.log("[ERROR] Cannot rotate foosmen row {} to angle {} since it is past min/max angle".format(self.id, angle))
            return

        # Need to rotate forward
        if angle > self.angle:
            numSteps = int((angle - self.angle) * self.stepsPerRevolution / 360)
            self.log("[MOTOR] Rotate row {} {} steps FORWARD to angle {}".format(self.id, numSteps, angle))
            for i in range(numSteps):
                self.rotateForward()

        # Need to rotate backward
        else:
            numSteps = int((self.angle - angle) * self.stepsPerRevolution / 360)
            self.log("[MOTOR] Rotate row {} {} steps BACKWARD to angle {}".format(self.id, numSteps, angle))
            for i in range(numSteps):
                self.rotateBackward()


    # Print output message to console
    def log(self, msg):
        print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"), msg)
