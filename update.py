from batch_monitor.models import BatchHostSettings
from batch_monitor.farms.farm_abstract import UserData, JobData, TimeData

import datetime, time
import collections
import threading, subprocess, subprocess32
import importlib, inspect

from django.core.cache import cache

g_users = None
g_user_total = None

def import_modules(remote, fsengine, farmengine):
	fs_obj = None
	farm_obj = None

	if fsengine is not None:
		modname = "batch_monitor.farms."+fsengine
		module = importlib.import_module(modname)
		clsmembers = inspect.getmembers(module, inspect.isclass)
		for m in clsmembers:
			if m[1].__module__ == modname:
				fs_class = getattr(module, m[0])
				fs_obj = fs_class(remote)

	if farmengine is not None:
		modname = "batch_monitor.farms."+farmengine
		module = importlib.import_module(modname)
		clsmembers = inspect.getmembers(module, inspect.isclass)
		for m in clsmembers:
			if m[1].__module__ == modname:
				fs_class = getattr(module, m[0])
				farm_obj = fs_class(remote)

	return fs_obj, farm_obj

def fetch_data(fs_obj, farm_obj, countdown=0):
	co1 = ""
	co2 = ""
	errno1 = 255
	errno2 = 255

	if fs_obj:
		co1, errno1 = fs_obj.fetch()

	if farm_obj:
		co2, errno2 = farm_obj.fetch()

	return co1, co2, errno1, errno2

def parse_data(fs_obj, farm_obj, jobs_list, users_list):
	co1 = ""
	co2 = ""
	errno1 = 255
	errno2 = 255

	if fs_obj:
		_users = fs_obj.parse()
		for u in xrange(len(_users)):
			_u = _users[u]
			if _u.name not in users_list:
				print("Adding user " + _uname)
				users_list[_u.name] = _u

	if farm_obj:
		_jobs = farm_obj.parse()

		update_jobs_list(jobs_list, users_list, _jobs)
		validate_jobs_list(jobs_list, users_list)
		cleanup_jobs_list(jobs_list, users_list)

def update_jobs_list(jobs_list, users_list, last_jobs):
	""" job list length to iterate on """
	job_list_len = len(jobs_list)
	""" counts jobs checked in the input list """
	job_cnt = 0


	""" if no jobs in the last check, all previous jobs are done """
	last_jobs_len = len(last_jobs)

	if not last_jobs_len:
		for i in xrange(job_list_len):
			jobs_list[i].mark_done()
		return

	for jd in last_jobs:
		""" update users list, in case that fair_share system is not working """
		""" FIXME: move to separate function """
		if jd.name not in users_list:
			print("Adding user " + jd.name)
			users_list[jd.name] = UserData(jd.name)

		while True:
			""" we reached end of the list, this job must be new then """
			if job_cnt == job_list_len:
				#print(" Adding job %d" % jd.jid)
				#jd = JobData(jid, _user, _farm, _status, _reqtime, _elatime)
				jobs_list.append(jd)
				break

			else:
				""" if jid is smaller than jid of current job """
				if jobs_list[job_cnt].jid < jd.jid:
					#print(" Removing job %d" % jobs_list[job_cnt].jid)
					""" otherwise job we are comparing to is finished
					mark as done and jump to next one """
					jobs_list[job_cnt].mark_done()
					#print(jd)
					job_cnt += 1
					continue

					""" update status of the job and break loop """
				elif jobs_list[job_cnt].jid == jd.jid:
					#print(" Updating job %d" % jobs_list[job_cnt].jid)
					jobs_list[job_cnt].update_status(jd)
					#print(jd)
					job_cnt += 1
					break

				else:
					print("Something went wrong with JID=%d..." % jid)
					break

	while job_cnt < job_list_len:
		#print(" Removing finished job %d" % jobs_list[job_cnt].jid)
		jobs_list[job_cnt].mark_done()
		job_cnt += 1

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

			if jobs_list[i].farm[0:5] == "farmq":
				_user.l_jobprogress.append([jobs_list[i].requested(), jobs_list[i].progress()])

		elif jobs_list[i].is_hold():
			_user.njobsH += 1
			_user.njobsT += 1
			total_hold += 1

	user_total = users_list['ALL']
	user_total.njobsR = total_run
	user_total.njobsQ = total_queued
	user_total.njobsH = total_hold
	user_total.njobsT = total_run + total_queued + total_hold

	for u in users_list:
		users_list[u].fill()

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

	if farm.fs_engine == "":
		fsengine_name = None
	else:
		fsengine_name = farm.fs_engine

	if farm.farm_engine == "":
		farmengine_name = None
	else:
		farmengine_name = farm.farm_engine

	fs_obj, farm_obj = import_modules(remote, fsengine_name, farmengine_name)

	dia_out, qst_out, dia_errno, qst_errno = fetch_data(fs_obj, farm_obj)

	if (fs_obj != None and dia_errno != 0) or (farm_obj != None and qst_errno != 0):
		return False

	g_users = cache.get("users_list", None)
	if g_users is None:
		g_users = collections.OrderedDict()
		g_users['ALL'] = UserData('All users')

	g_user_total = g_users['ALL']

	g_jobs = cache.get("jobs_list", [])

	parse_data(fs_obj, farm_obj, g_jobs, g_users)
	#parse_diagnose(dia_out, g_users)
	#parse_qstat(qst_out, g_jobs)

	#validate_jobs_list(g_jobs, g_users)
	#cleanup_jobs_list(g_jobs, g_users)

	g_view_list = []
	g_view_list.append('ALL')

	for u in g_users.keys():
		#g_users[u].fill()

		val = g_users[u]

		if val.viscnt > 0:
			if u != 'ALL':
				g_view_list.append(u)

	cache.set("time_stamp", g_ts)
	cache.set("users_list", g_users)
	cache.set("jobs_list", g_jobs)
	cache.set("views_list", g_view_list)

	return True