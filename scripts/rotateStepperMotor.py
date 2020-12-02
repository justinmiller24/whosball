###########################
# Run Motor script        #
###########################

# This script is used to test stepper motors with the TB6600 driver
# Created by Justin Miller on 11.30.2020
# https://www.instructables.com/Raspberry-Pi-Python-and-a-TB6600-Stepper-Motor-Dri/
# https://learn.adafruit.com/adafruit-dc-and-stepper-motor-hat-for-raspberry-pi/powering-motors

# USAGE:
# python3 rotateStepperMotor.py

# The TB6600 is a high voltage 2 phase stepper motor driver with current control.
# The driver microsteps up to 32 steps, outputs 3.5A to motors, and takes up to 42V of VCC.
# This makes the TB6600 an ideal candidate for high power and high precision applications.
# The 5V input current is ideal for RaspberryPi and Arduino applications.

# NEMA 17 Stepper Motor
# Motor type: Bipolar Stepper
# Phase Resistance: 1.5Ohm
# Phase Inductance: 2.8mH
# Detent Torque: 2.2N.cm
# Rotor Inertia: 54g.cm2
# Holding Torque: 40N.cm
# Step angle: 1.8 deg
# Motor Weight: 280g
# Step angle accuracy: + - 5%(full step, not load)
# Resistance accuracy: + - 10%
# Inductance accuracy: + - 20%
# Temperature rise: 80deg Max(rated current, 2 phase on)
# Ambient temperature: —20deg ~+50deg
# Insulation resistance: 100MΩ Min, 500VDC
# Insultion Strength: 500VAC for one minute
# Connection: Red(A+), Green(A-), Yellow(B+), Blue(B-)

# Current Specs
# 200 steps/rev
# 24V
# 1.7A
# TB6600 driver = 1:1 microstep mode
# Number of steps to turn one full revolution = 200

# Import packages
import RPi.GPIO as io
import time

# Global variables
STEPS_PER_REV = 200     # The number of steps needed for one full revolution
DELAY = .0022           # Delay time, in seconds

# GPIO pins
STP = 17                # Step
DIR = 27                # Direction
ENA = 22                # Enable

# Use broadcom pin-numbering scheme for GPIO pins
# These pin numbers follow the lower-level numbering system defined by the Raspberry Pi's Broadcom-chip brain
io.setmode(io.BCM)

# Set pin modes for 3 GPIO pins used
io.setup(STP, io.OUT)
io.setup(DIR, io.OUT)
io.setup(ENA, io.OUT)

# Set direction (CW = True, CCW = False)
io.output(DIR, 1)

# Start motor - power IS going to the motor
io.output(ENA, 0)

for pin in [17, 27, 22]:
    if io.input(pin):
        print("GPIO pin {} is HIGH".format(pin))
    else:
        print("GPIO pin {} is LOW".format(pin))

# Main Loop
print("Rotate 360 degrees = {} steps".format(STEPS_PER_REV))
for x in range(STEPS_PER_REV):
    io.output(STP, 1)
    time.sleep(DELAY)
    io.output(STP, 0)
    time.sleep(DELAY)

# Stop motor - power is NOT going to the motor
io.output(ENA, 1)

# Clear GPIO settings
io.cleanup()
