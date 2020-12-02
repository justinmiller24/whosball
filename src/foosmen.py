#########################
# Automated Foosball    #
#########################

# This class handles all of the foosmen
# Each row of foosmen has two motors, one for linear motion and one for rotational motion
# https://www.instructables.com/Raspberry-Pi-Python-and-a-TB6600-Stepper-Motor-Dri/

# Import packages
import RPi.GPIO as io
import time


class Foosmen:

    # Initialize foosmen row
    def __init__(self, id, numPlayers, xPos, playerSpacing, maxLinearMovement, linearIO, rotationalIO):

        # The ID of each foosmen row goes from left to right (0-7)
        self.id = id

        # The number of foosmen on each row
        self.players = numPlayers

        # The width of each foosmen (in pixels)
        self.playerWidth = 14

        # The position of the foosmen row (xPosition)
        self.xPos = xPos

        # The number of pixels between two players on each row
        self.playerSpacing = playerSpacing

        # The spanning distance (linear movement) that each player can move (in pixels)
        self.maxPosition = maxLinearMovement

        # The current position (linear movement)
        # 0 = all the way towards the side with the motors
        self.position = 0

        # Both motors exist and initialized
        self.linearMotorExists = False
        self.rotationalMotorExists = False

        # The number of steps per pixel, used for linear motion
        self.pixelsPerStep = 1

        # Calculate center position (linear motion)
        self.centerPosition = int((self.maxPosition / self.pixelsPerStep) / 2)

        # The number of steps needed for one full 360 degree revolution (rotational motion)
        self.stepsPerRevolution = 200

        # The time delay needed (in seconds) between pulses, to ensure continuous movement
        # This ensure continuous movement and effectively sets the rotation speed of the motor
        self.delay = .0022


        ##########################################################################
        # Initialize linear and rotational motors                                #
        ##########################################################################

        # Use broadcom pin-numbering scheme for GPIO pins
        # These pin numbers follow the lower-level numbering system defined by the Raspberry Pi's Broadcom-chip brain
        io.setmode(io.BCM)


        # Linear Motion
        # Set pin modes for 3 GPIO pins used
        if linearIO is not None:

            # Pulse/Step
            self.linearPUL = linearIO[0]
            io.setup(self.linearPUL, io.OUT)

            # Direction
            self.linearDIR = linearIO[1]
            io.setup(self.linearDIR, io.OUT)

            # Enable
            self.linearENA = linearIO[2]
            io.setup(self.linearENA, io.OUT)

            self.linearMotorExists = True


        # Rotational Motion
        # Set pin modes for 3 GPIO pins used
        if rotationalIO is not None:

            # Pulse/Step
            self.rotationalPUL = rotationalIO[0]
            io.setup(self.rotationalPUL, io.OUT)

            # Direction
            self.rotationalDIR = rotationalIO[1]
            io.setup(self.rotationalDIR, io.OUT)

            # Enable
            self.rotationalENA = rotationalIO[2]
            io.setup(self.rotationalENA, io.OUT)

            self.rotationalMotorExists = True


    # Initialize motors and warm up
    def start(self):

        # Linear motor
        if self.linearMotorExists:
            # Set direction
            io.output(self.linearDIR, 1)
            # Send power
            io.output(self.linearENA, 0)

        # Rotational motor
        if self.rotationalMotorExists:
            # Set direction
            io.output(self.rotationalDIR, 1)
            # Send power
            io.output(self.rotationalENA, 0)

        return self


    # Stop motors
    def stop(self):
        if self.linearMotorExists:
            io.output(self.linearENA, 1)
        if self.rotationalMotorExists:
            io.output(self.rotationalENA, 1)


    # Kick foosmen row (rotational motion)
    def kick(self):

        # Ensure motor exists
        if not self.rotationalMotorExists:
            return

        #io.output(self.rotationalDIR, 1)
        for x in range(self.stepsPerRevolution):
            io.output(self.rotationalPUL, 1)
            time.sleep(self.delay)
            io.output(self.rotationalPUL, 0)
            time.sleep(self.delay)


    # Move to center position - this is the default defensive position (linear motion)
    def center(self):
        self.moveTo(self.centerPosition)


    # Move linear motors to specific position
    def moveTo(self, pos):

        # Ensure motor exists
        if not self.linearMotorExists:
            return

        # Need to move forward
        if (self.position < pos):
            io.output(self.linearDIR, 1)
        # Need to move backward
        else
            io.output(self.linearDIR, 0)

        # Calculate number of steps needed and move
        steps = abs((pos - self.position) / self.pixelsPerStep)
        for i in range(steps):
            io.output(self.linearPUL, 1)
            time.sleep(self.delay)
            io.output(self.linearPUL, 0)
            time.sleep(self.delay)
