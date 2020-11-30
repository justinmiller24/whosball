###########################
# Run Motor script        #
###########################

# This script is used to test stepper motors with the TB6600 driver
# Created by Justin Miller on 11.30.2020
# https://www.instructables.com/Raspberry-Pi-Python-and-a-TB6600-Stepper-Motor-Dri/

# USAGE:
# python3 runMotors.py

# The TB6600 is a high voltage 2 phase stepper motor driver with current control.
# The driver microsteps up to 32 steps, outputs 3.5A to motors, and takes up to 42V of VCC.
# This makes the TB6600 an ideal candidate for high power and high precision applications.
# The 5V input current is ideal for RaspberryPi and Arduino applications.

# Current Specs
#200 steps/rev
#24V, 1.7A
#TB6600 driver = 1:1 microstep mode
#Turn a 200 step motor left one full revolution: 200

# Import packages
from time import sleep
import RPi.GPIO as gpio

# Global variables
STEPS_PER_REVOLUTION = 200  # The number of steps needed for one full revolution
DELAY = .002    # Delay time, in seconds
# GPIO pins
STP = 22    # Step
DIR = 23    # Direction
ENA = 24    # Enable

# Use broadcom layout for the GPIO
gpio.setmode(gpio.BCM)
gpio.setup(STP, gpio.OUT)
gpio.setup(DIR, gpio.OUT)
gpio.setup(ENA, gpio.OUT)

# Set direction (CW = true, CCW = false)
#gpio.output(DIR, True)
gpio.output(DIR, 1)

# Start motor - power IS going to the motor
#gpio.output(ENA, True)
gpio.output(ENA, 1)

# Main Loop
for x in range(STEPS_PER_REVOLUTION):
    #GPIO.output(STP, gpio.HIGH)
    GPIO.output(STP, 1)
    time.sleep(DELAY)
    GPIO.output(STP, 0)
    time.sleep(DELAY)
    print("Move one step")

# Stop motor - power is NOT going to the motor
gpio.output(ENA, 0)

# Clear GPIO settings
gpio.cleanup()
