#########################
# Whosball Controller   #
#########################

# This is the main whosball class

# Import packages
from datetime import datetime as dt

class whosball:

	def __init__(self):
		log('******************************')
		log('*****    WHOSBALL v1.0   *****')
		log('******************************')
		log('')
		log('')
		self.status = 'Initialized'

	def start(self):
		self.status = 'Started'

	def end(self):
		self.status = 'Ended'

	def getStatus(self):
		log('Status:', self.status)

def log(msg):
	print(dt.now(), msg)
