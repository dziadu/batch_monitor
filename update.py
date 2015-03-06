from batch_monitor.models import BatchHostSettings, UserData, TimeData

import datetime, time
import collections
import threading, subprocess, subprocess32

from django.core.cache import cache

g_users = None
g_user_total = None
g_view_list = []

class Command(object):
	def __init__(self, tid, cmd):
		self.tid = tid
		self.cmd = cmd
		self.process = None
		self.thread = None
		self.cout = None
		self.cerr = None
		self.terminated = False

	def run(self):
		def target():
			self.process = subprocess32.Popen(self.cmd, shell=True, stdout=subprocess32.PIPE, stderr=subprocess32.PIPE)
			self.cout, self.cerr = self.process.communicate()

		self.thread = threading.Thread(target=target)
		self.thread.start()

	def check(self, timeout):
		self.thread.join(timeout)
		if self.thread.is_alive():
			print("Terminating " + self.tid + " process: " + self.cmd)
			self.process.terminate()
			#self.thread.join()
			self.terminated = True

		return self.cout, self.cerr, self.terminated

def fetch_data(remote, countdown=10):
	if remote is not None:
		cmd1 = "{:s} diagnose -f".format(remote)
		cmd2 = "{:s} qstat -n -1".format(remote)
		#cmd1 = "cat batch_monitor/diagnose.txt;"
		#cmd2 = "cat batch_monitor/qstat.txt"
	else:
		cmd = "diagnose -f"
		cmd = "qstat -n -1"
		#cmd1 = "cat batch_monitor/diagnose.txt;"
		#cmd2 = "cat batch_monitor/qstat.txt"

	command1 = Command("p1", cmd1)
	command2 = Command("p2", cmd2)

	while True:
		command1.run()
		command2.run()

		co1, ce1, ter1 = command1.check(timeout=2)
		co2, ce2, ter2 = command2.check(timeout=2)

		if countdown == 0 or not ter1 and not ter2:
			break
		else:
			countdown -=1

	return co1, co2

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

def parse_diagnose(data):
	global g_users, g_user_total

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

				if _uname not in g_users:
					print("Adding user " + _uname)
					g_users[_uname] = UserData(_uname)

				_fair = float(words[1])
				g_users[_uname].clear()
				g_users[_uname].fairshare = 100.0 - _fair

def parse_qstat(data):
	global g_users, g_user_total
	text = data

	_waitline=0
	_parse_jobs = False

	for line in text.splitlines():
		_l = line.split()
		if len(_l) and _l[0] == "Job":
			_parse_jobs = True
			_waitline = 1
			continue

		if not _parse_jobs:
				continue
		else:
			if _waitline > 0:
				_waitline -= 1
				continue
			else:
				words = line.split()
				_jname = words[0]
				_uname = words[1]
				_fname = words[2]
				_rname = words[8]
				_sname = words[9]
				_ename = words[10]

				if _sname == "R":
					g_users[_uname].njobsR += 1
					g_user_total.njobsR += 1

					if _fname == "farmqe":

						if _ename == "--":
							_ename = "00:00"

						_time_r = _rname.split(":")
						_mins_r = int(_time_r[0]) * 60 + int(_time_r[1])
						_time_e = _ename.split(":")
						_mins_e = int(_time_e[0]) * 60 + int(_time_e[1])

						_time_progress = float(_mins_e) / _mins_r
						g_users[_uname].l_jobprogress.append([_mins_r, _time_progress])

				if _sname == "H":
					g_users[_uname].njobsH += 1
					g_user_total.njobsH += 1

				if _sname == "Q":
					g_users[_uname].njobsQ += 1
					g_user_total.njobsQ += 1

def parse_farm(farm):
	global g_users, g_user_total, g_view_list

	if farm.host == "localhost":
		remote = None
	else:
		remote = "ssh -p {:d} {:s}@{:s}".format(farm.port, farm.user, farm.host)

	g_ts = cache.get("time_stamp", None)
	if g_ts is None:
		g_ts = TimeData()

	g_ts.ts.append(time.mktime(datetime.datetime.now().timetuple()) * 1000)

	#dia_out = fetch_diagnose(remote)
	#qst_out = fetch_qstat(remote)

	dia_out, qst_out = fetch_data(remote)

	if dia_out is None or qst_out is None:
		return False

	dia_out = dia_out.decode("UTF-8")
	qst_out = qst_out.decode("UTF-8")

	g_users = cache.get("user_list", None)
	if g_users is None:
		g_users = collections.OrderedDict()
		g_users['ALL'] = UserData('All users')

	g_user_total = g_users['ALL']
	g_user_total.clear()

	parse_diagnose(dia_out)
	parse_qstat(qst_out)

	del g_view_list[:]
	g_view_list.append('ALL')

	for u in g_users.keys():
		g_users[u].fill()

		val = g_users[u]

		if val.viscnt > 0:
			if u != 'ALL':
				g_view_list.append(u)

	cache.set("time_stamp", g_ts)
	cache.set("user_list", g_users)
	cache.set("view_list", g_view_list)

	return True