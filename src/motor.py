from adafruit_motorkit import MotorKit


def determineMove():
	out("Determine which motors to move")


def move():
	out("Move motors")

	# Initialise the first hat on the default address
	# Stepper motors are available as stepper1 and stepper2
	# stepper1 is made up of the M1 and M2 terminals
	# stepper2 is made up of the M3 and M4 terminals
	#self.motors.kit1 = Motorkit().stepper1
	#self.motors.kit2 = Motorkit().stepper2

	# Initialise the second hat on a different address
	#self.motors.kit3 = MotorKit(address=0x61).stepper1
	#self.motors.kit4 = MotorKit(address=0x61).stepper2

	# https://learn.adafruit.com/adafruit-dc-and-stepper-motor-hat-for-raspberry-pi/using-stepper-motors
	#self.motors.kit1.stepper1.onestep()
