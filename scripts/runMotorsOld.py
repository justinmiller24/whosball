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
#import curses

STEPS_PER_REVOLUTION = 200


# Define GPIO pins
# Use broadcom layout for the GPIO
gpio.setmode(gpio.BCM)
# Step
STP = 22
gpio.setup(STP, gpio.OUT)
# Direction
DIR = 23
gpio.setup(DIR, gpio.OUT)
# Enable
ENA = 24
gpio.setup(ENA, gpio.OUT)

# Delay time in between steps
DELAY = .002

# Set direction
# T = Clockwise
# F = Counter clockwide
gpio.output(DIR, True)

# Start motor
# Power IS going to the motor
gpio.output(ENA, True)

# Main Loop
for x in range(STEPS_PER_REVOLUTION):
    #GPIO.output(STP, 1)
    GPIO.output(STP, gpio.HIGH)
    time.sleep(DELAY)
    #GPIO.output(STP, 0)
    GPIO.output(STP, gpio.LOW)
    time.sleep(DELAY)
    print("Move one step")

# Stop motor
# Power is NOT going to the motor
gpio.output(ENA, False)

# Clear GPIO settings
gpio.cleanup()



# # Function to step the motor
# # steps = number of steps to take
# # dir = direction stepper will move (R or L)
# # speed = defines the denominator in the waitTime equation: waitTime = 0.000001/speed. As "speed" is increased, the waitTime between steps is lowered
# # stayOn = defines whether or not stepper should stay "on" or not. If stepper will need to receive a new step command immediately, this should be set to "True." Otherwise, it should remain at "False."
# def step(pins, steps, dir='R', speed=1):
#
#     #set the output to true for left and false for right
#     if (dir == 'R'):
#         gpio.output(pins[1], False)
#     else:
#         gpio.output(pins[1], True)
#
#     # Count number of steps and control speed
#     stepCounter = 0
#     waitTime = 0.000001 / speed
#
#     # Loop through number of steps
#     while stepCounter < steps:
#
#         # Take one step by toggling GPIO on/off as input to motor driver
#         gpio.output(pins[0], True)
#         gpio.output(pins[0], False)
#         stepCounter += 1
#
#         # Control rotation speed by waiting before taking the next step
#         sleep(waitTime)
#
#     # Stop motor (ie, power is NOT going to the motor)
#     gpio.output(pins[2], True)
#
#     print("Stepper Driver complete (turned " + dir + " " + str(steps) + " steps)")
#     return
#
#
#
# print("Initialized. Use the following keys for control\n")
# print("WASD: controlling X and Y motors\n")
# print("  QE: raising and lowering Z motor\n")
# print("   X: to quit the program\n")
#
# screen = curses.initscr()
#
# while True:
#     c = screen.getch()
#     time.sleep(0.03)
#     if c == ord('w'):
#         pulse_x_ccw()
#     elif c == ord('s'):
#         pulse_x_cw()
#     elif c == ord('a'):
#         pulse_y_ccw()
#     elif c == ord('d'):
#         pulse_y_cw()
#     elif c == ord('q'):
#         pulse_z_ccw()
#     elif c == ord('e'):
#         pulse_z_cw()
#     elif c == ord('z'):
#         servo_left()
#     elif c == ord('c'):
#         servo_right()
#     elif c == ord('x'):
#         servo_stop()
#     elif c == ord('r'):
#         break  # Exit the while loop
