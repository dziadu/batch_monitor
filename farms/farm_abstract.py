import datetime, time
import threading, subprocess, subprocess32

from collections import deque
from django.conf import settings

if hasattr(settings, 'BATCH_FARM_CALCTIME_LEN'):
	calctime_len=int(settings.BATCH_FARM_CALCTIME_LEN)
else:
	calctime_len=500

if hasattr(settings, 'BATCH_FARM_DEQUE_LEN'):
	deque_len=int(settings.BATCH_FARM_DEQUE_LEN)
else:
	deque_len = 12 * 60 * 1

class TimeData():
	def __init__(self):
		self.colsize = deque_len
		self.ts = deque(maxlen=deque_len)

class UserData():
	def __init__(self, name):
		self.name = name
		self.viscnt = 0
		self.q_njobsT = deque(maxlen=deque_len)
		self.q_njobsR = deque(maxlen=deque_len)
		self.q_njobsH = deque(maxlen=deque_len)
		self.q_njobsQ = deque(maxlen=deque_len)
		self.q_fairshare = deque(maxlen=deque_len)
		self.l_jobprogress = []
		self.q_calctime = deque(maxlen=calctime_len)

		self.njobsT = 0
		self.njobsR = 0
		self.njobsH = 0
		self.njobsQ = 0
		self.fairshare = 100.0

	def clear(self):
		self.njobsT = 0
		self.njobsR = 0
		self.njobsH = 0
		self.njobsQ = 0
		#self.fairshare = 100.0
		del self.l_jobprogress[:]

	def fill(self):
		self.njobsT = self.njobsR + self.njobsH + self.njobsQ

		self.q_njobsT.append(self.njobsT)
		self.q_njobsR.append(self.njobsR)
		self.q_njobsH.append(self.njobsH)
		self.q_njobsQ.append(self.njobsQ)
		self.q_fairshare.append(self.fairshare)

		#if self.njobsT > 0:
			#self.viscnt = deque_len
		#elif self.viscnt > 0:
			#self.viscnt -= 1

		if self.q_fairshare < 100.0:
			self.viscnt = deque_len
		else:
			if self.njobsT > 0:
				self.viscnt = deque_len
			elif self.viscnt > 0:
				self.viscnt -= 1

class JobData():
	def __init__(self, jid, name, farm, status, req_time, ela_time):
		self.jid = jid
		self.name = name
		self.farm = farm
		self.req_time = req_time
		self.ela_time = ela_time
		# 0 - queued, 1 - run, 2 - hold, 3 - finished
		self.status = status

	def requested(self):
		return self.req_time

	def progress(self):
		if (self.req_time):
			return float(self.ela_time)/self.req_time
		else:
			return 1.1

	def calc_time(self):
		return self.ela_time/60

	def mark_done(self):
		self.status = 3

	def is_queued(self):
		return self.status == 0

	def is_running(self):
		return self.status == 1

	def is_hold(self):
		return self.status == 2

	def is_done(self):
		return self.status == 3

	def update_status(self, job):
		self.status = job.status
		self.ela_time = job.ela_time

	def __str__(self):
		return "JID: {:d} NAME: {:s} FARM: {:s} REQ: {:d} STA: {:d} ELA: {:d}".format(self.jid, self.name, self.farm, self.req_time, self.status, self.ela_time)

class Command(object):
	def __init__(self, tid, cmd):
		self.tid = tid
		self.cmd = cmd
		self.process = None
		self.thread = None
		self.cout = None
		self.cerr = None
		self.errno = 0
		self.terminated = False

	def run(self):
		def target():
			self.process = subprocess32.Popen(self.cmd, shell=True, stdout=subprocess32.PIPE, stderr=subprocess32.PIPE)
			self.cout, self.cerr = self.process.communicate()
			self.errno = self.process.returncode

		self.thread = threading.Thread(target=target)
		self.thread.start()

	def check(self, timeout):
		self.thread.join(timeout)
		if self.thread.is_alive():
			print("Terminating " + self.tid + " process: " + self.cmd + " at " + datetime.datetime.now())
			self.process.terminate()
			#self.thread.join()
			self.terminated = True

		return self.cout, self.cerr, self.terminated, self.errno

class FairShareEngine(object):
	def __init__(self, remote):
		self.remote = remote
		self.data = None
		self.cmd = None

	def fetch(self):
		remote_cmd = "{:s} {:s}".format(self.remote, self.cmd)
		command = Command("farm command", remote_cmd)
		command.run()
		co, ce, ter, errno = command.check(timeout=2)

		self.data = co.decode("UTF-8")
		return self.data, errno

	def parse(self):
		return []

class FarmEngine(object):
	def __init__(self, remote):
		self.remote = remote
		self.data = None
		self.cmd = None

	def fetch(self):
		remote_cmd = "{:s} {:s}".format(self.remote, self.cmd)
		command = Command("farm command", remote_cmd)
		command.run()
		co, ce, ter, errno = command.check(timeout=2)

		self.data = co.decode("UTF-8")
		return self.data, errno

	def parse(self):
		return []

	def strtime2secs(self, text):
		return 0

	def status_decode(self, status):
		return 3
