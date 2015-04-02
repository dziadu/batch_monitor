from batch_monitor.farms.farm_abstract import Command, JobData, FarmEngine

g_users = None
g_user_total = None

class Slurm(FarmEngine):
	def __init__(self, remote):
		super(Slurm, self).__init__(remote)
		self.cmd = "squeue -S i -o \\\"%A %u %P %l %T %M\\\""

	def parse(self):
		text = self.data
		jobs_list = []

		_waitline=0
		_parse_jobs = False

		for line in text.splitlines():
			_l = line.split()
			if len(_l) and _l[0] == "JOBID":
				_parse_jobs = True
				_waitline = 0
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
					_reqtime	= words[3]
					_status		= words[4]
					_elatime	= words[5]

					jid = int(_jid)

					jd = JobData(jid, _user, _farm,
						self.status_decode(_status),
						self.strtime2secs(_reqtime),
						self.strtime2secs(_elatime))
					jobs_list.append(jd)

		return jobs_list

	def strtime2secs(self, text):
		if text == "UNLIMITED":
			text = "99:99:99"
		if text == "NOT_SET":
			text = "00:00:00"

		time = text.split(":")
		_len = len(time)

		total_time = int(time[_len-1])

		for i in xrange(_len-2,-1,-1):
			total_time += int(time[i]) * 60

		return total_time

	def status_decode(self, status):
		if status == "PENDING":
			return 0
		elif status == "RUNNING":
			return 1
		elif status == "SUSPENDED":
			return 2
