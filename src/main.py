#########################
# Automated Foosball    #
#########################

# This is the main script for the Automted Foosball game
# Created by Justin Miller on 2.17.2020

# USAGE:
# python3 main.py

# Import packages
import os
import time
from whosball import whosball

# Console log
print('')
print('Loading...')
print('')

# Clear screen
time.sleep(1)
os.system('cls||clear')

# Initialize game
w = whosball()

# Initialize camera
