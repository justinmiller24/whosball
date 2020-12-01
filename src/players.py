#########################
# Automated Foosball    #
#########################

# This class handles all of the foosmen
# Each row of foosmen has two motors, one for linear motion and one for rotational motion
# https://projects.raspberrypi.org/en/projects/physical-computing/14
# https://gpiozero.readthedocs.io/en/stable/recipes.html

# import the necessary packages
from gpiozero import Motor
import datetime
import time


class Foosmen:

    # Initialize foosmen row
    def __init__(self, id, numPlayers, linearMotorAddr, rotationalMotorAddr, playerSpacing, rowLength, playerWidth):

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

        # The GPIO addresses for each motor
        self.linearMotorAddr = linearMotorAddr
        self.rotationalMotorAddr = rotationalMotorAddr

        # Both motors exist and initialized
        self.motorsExist = False

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

        # The number of milliseconds per step
        self.stepTimeInMs = .0208


    # Initialize motors and warm up
    def start(self):

        ##########################################################################
        # This section initializes the linear and rotational motors              #
        ##########################################################################

        # Linear Motion
        if self.linearMotorAddr is not None:
            self.motor1 = Motor(self.linearMotorAddr[0], self.linearMotorAddr[1])
            self.log("[MOTOR] Initialized foosmen row {} linear motor from GPIO ({}, {})".format(self.id, self.linearMotorAddr[0], self.linearMotorAddr[1]))
        else:
            self.log("[ERROR] Could not initialize linear motor on foosmen row {}".format(self.id))
            return self

        # Rotational Motion
        if self.rotationalMotorAddr is not None:
            self.motor2 = Motor(self.rotationalMotorAddr[0], self.rotationalMotorAddr[1])
            self.log("[MOTOR] Initialized foosmen row {} rotational motor from GPIO ({}, {})".format(self.id, self.rotationalMotorAddr[0], self.rotationalMotorAddr[1]))
        else:
            self.log("[ERROR] Could not initialize rotational motor on foosmen row {}".format(self.id))
            return self

        self.motorsExist = True

        # Release motors so they can spin freely
        #self.motors.stepper1.release()
        #self.motors.stepper2.release()

        # Warm up motors
        self.log("[MOTOR] Warm up linear motor")
        self.motor1.forward()
        time.sleep(.005)
        self.motor1.backward()
        time.sleep(.005)
        self.motor1.stop()

        self.log("[MOTOR] Warm up rotational motor")
        self.motor2.forward()
        time.sleep(.005)
        self.motor2.backward()
        time.sleep(.005)
        self.motor2.stop()

        return self


    # Set to default defensive position
    def defaultPosition(self):
        return


    # Move linear motor and rotational motor to kick the foosball at an angle
    # Determine if we need to move left/right/none based on angle (Y/X ratio)
    def kickAngle(self, angle, x, y):
        if not self.motorsExist:
            self.log("[MOTOR] Skipping kickAngle({}, {}) - motors do not exist".format(x,y))
            return

        self.log("[MOTOR] Kick row {} at angle {}".format(self.id, angle))
        self.log("[MOTOR] Move {}px X axis and {}px Y axis".format(x, y))

        # Setup shot
        angle = 75
        numSteps = int(float((angle - self.angle) * self.stepsPerRevolution / 360))
        self.log("[MOTOR] Setup shot, kick to 75 degree rotation requires {} steps".format(numSteps))

        # If shot angle is exactly 90 degrees, then we are vertically centered
        # and only need to kick straight ahead (rotational motion)
        if angle == 90:
            self.log("[MOTOR] Kick at 90 degree angle")
            # Kick to maximum angle (75 degrees forward)
            #self.rotateTo(75)
            self.motor2.forward()
            time.sleep(self.stepTimeInMs * numSteps / 1000)
            # Reset
            #self.rotateTo(0)
            self.motor2.reverse()
            time.sleep(self.stepTimeInMs * numSteps / 1000)
            # Stop motor
            self.motor2.stop()

        # If shot angle is not within +/- 45 degrees of center, then limit the
        # shot angle to +45 degrees or -45 degrees by moving both motors simultaneously
        elif angle <= 45 | angle >= 135:
            if angle <= 45:
                self.log("[MOTOR] Kick at 45 degree angle, move both motors simultaneously")
                self.motor1.forward()
            else:
                self.log("[MOTOR] Kick at 135 degree angle, move both motors simultaneously")
                self.motor1.backward()
            self.motor2.forward()
            time.sleep(self.stepTimeInMs * numSteps / 1000)
            # Reset
            self.motor1.reverse()
            self.motor2.reverse()
            time.sleep(self.stepTimeInMs * numSteps / 1000)
            # Stop motors
            self.motor1.stop()
            self.motor2.stop()

        # If shot angle is within +/- 45 degrees of center, then limit the
        # shot angle by calculating the Y/X ratio and using this percentage
        # to throttle the linear motion so the kick remains at full speed
        elif angle > 45 & angle < 135:
            throttleSpeed = abs(y/x)
            self.log("[MOTOR] Kick at {} degree angle, move both motors and throttle linear motion at {}%".format(angle, (throttleSpeed * 100)))
            #angle = 75
            #numSteps = int(float((angle - self.angle) * self.stepsPerRevolution / 360))

            # Rotational motion
            #self.angle += (360 / self.stepsPerRevolution * numSteps)

            # Linear motion
            #numLinearSteps = int(float(numSteps * throttleSpeed))
            #self.position += (self.pixelsPerStep * numLinearSteps)

            # If foosball is "above" vertical center line, then kick + move right
            if angle < 90:
                #self.log("[MOTOR] Move row {} {} steps FORWARD at {}% while kicking at 100%".format(self.id, numSteps, (throttleSpeed * 100)))
                self.motor1.forward(throttleSpeed)
            else:
                #self.log("[MOTOR] Move row {} {} steps FORWARD at {}% while kicking at 100%".format(self.id, numSteps, (throttleSpeed * 100)))
                self.motor1.backward(throttleSpeed)
            self.motor2.forward()
            time.sleep(self.stepTimeInMs * numSteps / 1000)
            # Reset
            self.motor1.reverse()
            self.motor2.reverse()
            time.sleep(self.stepTimeInMs * numSteps / 1000)
            # Stop motors
            self.motor1.stop()
            self.motor2.stop()

        # Something went wrong
        else:
            self.log("[ERROR] Something went wrong, exiting...")
            return


    # Move linear motor one step BACKWARD
    def moveBackward(self):
        if not self.motorsExist:
            self.log("[MOTOR] Skipping moveBackward() - motors do not exist")
            return


        # Make sure next position is not out of bounds
        if self.position < self.pixelsPerStep:
            self.log("[ERROR] Cannot move foosmen row since it is past min position")
            return

        # Move backward one step
        self.position -= self.pixelsPerStep
        self.motor1.backward()
        time.sleep(self.stepTimeInMs / 1000)
        self.motor1.stop()
        self.log("[MOTOR] Move row {} one step BACKWARD, position is now: {}".format(self.id, self.position))


    # Move linear motor one step FORWARD
    def moveForward(self):
        if not self.motorsExist:
            self.log("[MOTOR] Skipping moveForward() - motors do not exist")
            return

        # Make sure next position is not out of bounds
        if self.position + self.pixelsPerStep > self.maxPosition:
            self.log("[ERROR] Cannot move foosmen row since it is past max position")
            return

        # Move forward one step
        self.position += self.pixelsPerStep
        self.motor1.forward()
        time.sleep(self.stepTimeInMs / 1000)
        self.motor1.stop()
        self.log("[MOTOR] Move row {} one step FORWARD, position is now: {}".format(self.id, self.position))


    # Move linear motor to get to specific position
    def moveTo(self, pos):
        if not self.motorsExist:
            self.log("[MOTOR] Skipping moveTo({}) - motors do not exist".format(pos))
            return

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
            numSteps = int(float((pos - self.position) * self.pixelsPerStep))
            self.log("[MOTOR] Move row {} {} steps FORWARD to position {}".format(self.id, numSteps, pos))
            #for i in range(numSteps):
                #self.moveForward()
            self.position += (self.pixelsPerStep * numSteps)
            self.motor1.forward()
            time.sleep(self.stepTimeInMs * numSteps / 1000)
            self.motor1.stop()


        # Need to move backward
        else:
            numSteps = int(float((self.position - pos) * self.pixelsPerStep))
            self.log("[MOTOR] Move row {} {} steps BACKWARD to position {}".format(self.id, numSteps, pos))
            #for i in range(numSteps):
                #self.moveBackward()
            self.position -= (self.pixelsPerStep * numSteps)
            self.motor1.backward()
            time.sleep(self.stepTimeInMs * numSteps / 1000)
            self.motor1.stop()


    # Release motors so they can spin freely
    def releaseMotors(self):
        if not self.motorsExist:
            self.log("[MOTOR] Skipping releaseMotors() - motors do not exist")
            return

        #self.motors.stepper1.release()
        #self.motors.stepper2.release()
        self.motor1.stop()
        self.motor2.stop()
        #return


    # Move rotational motor one step BACKWARD
    def rotateBackward(self):
        if not self.motorsExist:
            self.log("[MOTOR] Skipping rotateBackward() - motors do not exist")
            return

        # Make sure next angle is not out of bounds
        # Min angle is -90 degrees
        # There are 200 steps per revolution, so each step is 1.8 degrees
        if self.angle < -88.2:
            self.log("[ERROR] Cannot rotate foosmen row since it is past min angle")
            return

        # Move backward one step
        # There are 200 steps per revolution, so each step is 1.8 degrees
        self.angle -= (360 / self.stepsPerRevolution)
        self.motor2.backward()
        time.sleep(self.stepTimeInMs / 1000)
        self.motor2.stop()
        self.log("[MOTOR] Rotate row {} one step BACKWARD, angle is now: {}".format(self.id, self.angle))


    # Move rotational motor one step FORWARD
    def rotateForward(self):
        if not self.motorsExist:
            self.log("[MOTOR] Skipping rotatteForward() - motors do not exist")
            return

        # Make sure next angle is not out of bounds
        # Max angle is +90 degrees
        # There are 200 steps per revolution, so each step is 1.8 degrees
        if self.angle > 88.2:
            self.log("[ERROR] Cannot rotate foosmen row since it is past max angle")
            return

        # Move forward one step
        # There are 200 steps per revolution, so each step is 1.8 degrees
        self.angle += (360 / self.stepsPerRevolution)
        self.motor2.forward()
        time.sleep(self.stepTimeInMs / 1000)
        self.motor2.stop()
        self.log("[MOTOR] Rotate row {} one step FORWARD, angle is now: {}".format(self.id, self.angle))


    # Move rotational motor to get to specific angle
    def rotateTo(self, angle):
        if not self.motorsExist:
            self.log("[MOTOR] Skipping rotateTo({}) - motors do not exist".format(angle))
            return

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
            numSteps = int(float((angle - self.angle) * self.stepsPerRevolution / 360))
            self.log("[MOTOR] Rotate row {} {} steps FORWARD to angle {}".format(self.id, numSteps, angle))
            #for i in range(numSteps):
                #self.rotateForward()
            self.angle += (360 / self.stepsPerRevolution * numSteps)
            self.motor2.forward()
            time.sleep(self.stepTimeInMs * numSteps / 1000)
            self.motor2.stop()

        # Need to rotate backward
        else:
            numSteps = int(float((self.angle - angle) * self.stepsPerRevolution / 360))
            self.log("[MOTOR] Rotate row {} {} steps BACKWARD to angle {}".format(self.id, numSteps, angle))
            #for i in range(numSteps):
                #self.rotateBackward()
            self.angle -= (360 / self.stepsPerRevolution * numSteps)
            self.motor2.backward()
            time.sleep(self.stepTimeInMs * numSteps / 1000)
            self.motor2.stop()


    # Print output message to console
    def log(self, msg):
        print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"), msg)
