from batch_monitor.models import JobData
from batch_monitor.farms.farm_abstract import Command, FarmEngine

class Qsub(FarmEngine):
	def __init__(self, remote):
		self.cmd = "qstat -n -1"
		self.super(remote)

	def parse(self):
		text = self.data
		jobs_list = []

		_waitline=0
		_parse_jobs = False

		""" job list length to iterate on """

		for line in text.splitlines():
			_l = line.split()
			if len(_l) and _l[0] == "Job":
				_parse_jobs = True
				_waitline = 1
				continue

			if _parse_jobs:
				if _waitline > 0:
					_waitline -= 1
					continue
				else:
					if len(line) == 0:
						continue

					words = line.split()

					if len(words) == 0:
						continue

					_jid		= words[0]
					_user		= words[1]
					_farm		= words[2]
					_reqtime	= words[8]
					_status		= words[9]
					_elatime	= words[10]

					jid = int(_jid.split('.')[0])

					jd = JobData(jid, _user, _farm,
						self.status_decode(_status),
						self.strtime2secs(_reqtime),
						self.strtime2secs(_elatime))
					jobs_list.append(jd)

	return jobs_list

	def strtime2secs(self, text):
		if text == "--":
			text = "00"

		time = text.split(":")
		_len = len(time)

		total_time = 0

		for i in xrange(_len-1,-1,-1)
			total_time += int(time[i]) * 60

		return total_time

	def status_decode(self, status):
		if status == "Q":
			return 0
		elif status == "R":
			return = 1
		elif status == "H":
			return = 2
