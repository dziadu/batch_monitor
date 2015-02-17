from django.db import models

from collections import deque

# Create your models here.
class BatchHostSettings(models.Model):
	name = models.CharField(max_length=200)
	host = models.CharField(max_length=200)
	user = models.CharField(max_length=200)
	port = models.IntegerField(default=22)
	sshpub = models.TextField()

class TimeData():
	def __init__(self):
		self.ts = deque(maxlen=12 * 60 * 1)

class UserData():
	def __init__(self):
		self.colsize = 12 * 60 * 1
		self.viscnt = 0
		self.q_njobsT = deque(maxlen=self.colsize)
		self.q_njobsR = deque(maxlen=self.colsize)
		self.q_njobsH = deque(maxlen=self.colsize)
		self.q_njobsQ = deque(maxlen=self.colsize)
		self.q_fairshare = deque(maxlen=self.colsize)
		self.l_jobprogress = []

		self.clear()

	def clear(self):
		self.njobsT = 0
		self.njobsR = 0
		self.njobsH = 0
		self.njobsQ = 0
		self.fairshare = 100.0
		del self.l_jobprogress[:]

	def fill(self):
		self.njobsT = self.njobsR + self.njobsH + self.njobsQ
		self.q_njobsT.append(self.njobsT)
		self.q_njobsR.append(self.njobsR)
		self.q_njobsH.append(self.njobsH)
		self.q_njobsQ.append(self.njobsQ)
		self.q_fairshare.append(self.fairshare)

		if self.njobsT > 0:
			self.viscnt = self.colsize
		elif self.viscnt > 0:
			self.viscnt -= 1