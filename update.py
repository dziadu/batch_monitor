from batch_monitor.models import BatchHostSettings, UserData, JobData, TimeData

import datetime, time
import collections
import threading, subprocess, subprocess32

from django.core.cache import cache

g_users = None
g_user_total = None

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

def fetch_data(remote, countdown=0):
	if remote is not None:
		cmd1 = "{:s} diagnose -f".format(remote)
		cmd2 = "{:s} qstat -n -1".format(remote)
	else:
		cmd1 = "diagnose -f"
		cmd2 = "qstat -n -1"

	#remote = None
	#cmd1 = "cat batch_monitor/diagnose.txt;"
	#cmd2 = "cat batch_monitor/qstat.txt"

	command1 = Command("p1", cmd1)
	command2 = Command("p2", cmd2)

	while True:
		command1.run()
		command2.run()

		co1, ce1, ter1, errno1 = command1.check(timeout=2)
		co2, ce2, ter2, errno2 = command2.check(timeout=2)

		if countdown == 0 or not ter1 and not ter2:
			break
		else:
			countdown -=1

	return co1, co2, errno1, errno2

def fetch_diagnose(remote):
	if remote is not None:
		cmd = "{:s} diagnose -f".format(remote)
	else:
		#cmd = "diagnose -f"
		cmd = "cat batch_monitor/diagnose.txt"

	proc = subprocess.Popen(
		cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
	)

	cout, cerr = proc.communicate()
	return cout

def fetch_qstat(remote):
	if remote is not None:
		cmd = "{:s} qstat -n -1".format(remote)
	else:
		#cmd = "qstat -n -1"
		cmd = "cat batch_monitor/qstat.txt"

	proc = subprocess.Popen(
		cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
	)

	cout, cerr = proc.communicate()
	return cout

def parse_diagnose(data, users_list):
	text = data

	_waitline=0
	_parse_user = False
	_parse_group = False

	for line in text.splitlines():
		if line == "USER":
			_parse_user = True
			_waitline = 1
			continue
		if line == "GROUP":
#			_parse_group = True
			_waitline = 1
			continue
		if line == "":
			_parse_user = _parse_group = False
			continue

		if _parse_user:
			if _waitline > 0:
				_waitline -= 1
			else:
				words = line.split()
				if words[0][-1] == "*":
					_uname = words[0][:-1]
				else:
					_uname = words[0]
				_uname = _uname[0:8]

				if _uname not in users_list:
					print("Adding user " + _uname)
					users_list[_uname] = UserData(_uname)

				_fair = float(words[1])
				users_list[_uname].clear()
				users_list[_uname].fairshare = 100.0 - _fair

def parse_qstat(data, jobs_list = []):
	text = data

	_waitline=0
	_parse_jobs = False

	""" job list length to iterate on """
	job_list_len = len(jobs_list)
	job_cnt = 0
	has_jobs = False

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

				has_jobs = True
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

				while True:

					""" we reached end of the list, this job must be new then """
					if job_cnt == job_list_len:
						#print(" Adding job %d" % jid)
						jd = JobData(jid, _user, _farm, _status, _reqtime, _elatime)
						jobs_list.append(jd)
						break

					else:
						""" if jid is smaller than jid of current job """
						if jobs_list[job_cnt].jid < jid:
							#print(" Removing job %d" % jobs_list[job_cnt].jid)
							""" otherwise job we are comparing to is finished
							mark as done and jump to next one """
							jobs_list[job_cnt].mark_done()
							job_cnt += 1
							continue

							""" update status of the job and break loop """
						elif jobs_list[job_cnt].jid == jid:
							#print(" Updating job %d" % jobs_list[job_cnt].jid)
							jobs_list[job_cnt].update_status(_status, _elatime)
							job_cnt += 1
							break

						else:
							print("Something went wrong with JID=%d..." % jid)

	if not has_jobs:
		for i in xrange(job_list_len):
			jobs_list[i].mark_done()

def validate_jobs_list(jobs_list, users_list):
	jobs_len = len(jobs_list)

	total_run = 0
	total_queued = 0
	total_hold = 0

	for u in users_list:
		users_list[u].clear()

	""" adding finished jobs to queue of calculation time """
	for i in xrange(jobs_len):

		_name = jobs_list[i].name
		_user = users_list[_name]

		if jobs_list[i].is_done():
			_user.q_calctime.append(jobs_list[i].calc_time())

		elif jobs_list[i].is_queued():
			_user.njobsQ += 1
			_user.njobsT += 1
			total_queued += 1

		elif jobs_list[i].is_running():
			_user.njobsR += 1
			_user.njobsT += 1
			total_run += 1

			if jobs_list[i].farm == "farmqe":
				_user.l_jobprogress.append([jobs_list[i].requested(), jobs_list[i].progress()])

		elif jobs_list[i].is_hold():
			_user.njobsH += 1
			_user.njobsT += 1
			total_hold += 1

	user_total = users_list['ALL']
	user_total.njobsR = total_run
	user_total.njobsQ = total_queued
	user_total.njobsH = total_hold
	user_total.njobsH = total_run + total_queued + total_hold

def cleanup_jobs_list(jobs_list, users_list):
	jobs_len = len(jobs_list)

	""" removing ranges instead of single jobs is more efficient
		this variables keeps beginning of the removing queue
		and flag is still valid """
	rm_queue_sta = -1
	rm_queue = False

	for i in xrange(jobs_len-1, -1, -1):
		if jobs_list[i].is_done():
			if rm_queue_sta == -1:
				rm_queue_sta = i
		else:
			if rm_queue_sta != -1:
				del jobs_list[i+1:rm_queue_sta+1]
				rm_queue_sta = -1

	if rm_queue_sta != -1:
		del jobs_list[0:rm_queue_sta+1]

def parse_farm(farm):
	global g_users, g_user_total

	if farm.host == "localhost":
		remote = None
	else:
		remote = "ssh -o 'BatchMode yes' -p {:d} {:s}@{:s}".format(farm.port, farm.user, farm.host)

	g_ts = cache.get("time_stamp", None)
	if g_ts is None:
		g_ts = TimeData()

	g_ts.ts.append(time.mktime(datetime.datetime.now().timetuple()) * 1000)

	#dia_out = fetch_diagnose(remote)
	#qst_out = fetch_qstat(remote)

	dia_out, qst_out, dia_errno, qst_errno = fetch_data(remote)

	if dia_errno != 0 or qst_errno != 0:
		return False

	#print(dia_out, qst_out)
	dia_out = dia_out.decode("UTF-8")
	qst_out = qst_out.decode("UTF-8")

	g_users = cache.get("users_list", None)
	if g_users is None:
		g_users = collections.OrderedDict()
		g_users['ALL'] = UserData('All users')

	g_user_total = g_users['ALL']

	g_jobs = cache.get("jobs_list", [])

	parse_diagnose(dia_out, g_users)
	parse_qstat(qst_out, g_jobs)

	validate_jobs_list(g_jobs, g_users)
	cleanup_jobs_list(g_jobs, g_users)

	g_view_list = []
	g_view_list.append('ALL')

	for u in g_users.keys():
		g_users[u].fill()

		val = g_users[u]

		if val.viscnt > 0:
			if u != 'ALL':
				g_view_list.append(u)

	cache.set("time_stamp", g_ts)
	cache.set("users_list", g_users)
	cache.set("jobs_list", g_jobs)
	cache.set("views_list", g_view_list)

	return True