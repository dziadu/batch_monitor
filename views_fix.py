from django.core.cache import cache
from batch_monitor.models import BatchHostSettings
from decorators import json_response
from django.shortcuts import get_object_or_404, render
#import json
import simplejson as json
# tools

def fix_data(request, farm_id):
	#data_series_tj = cache.get('data_trend_tj', [])
	#data_series_rj = cache.get('data_trend_rj', [])
	#data_series_fs = cache.get('data_trend_fs', [])
	#data_series_uct = cache.get('data_trend_uct', [])
	#data_hist_jct = cache.get('data_hist_jct', [])
	#data_dist_jp = cache.get('data_dist_jp', [])
	#data_group_tj = cache.get('data_tj_f', [])
	#data_group_rj = cache.get('data_rj_f', [])
	#data_group_qj = cache.get('data_qj_f', [])

	#g_ts = cache.get("time_stamp", None)

	#if g_ts is not None:
		#data_list_ts = list(g_ts.ts)

	g_users = cache.get("users_list", None)

	_vl = cache.get("views_list", None)
	if _vl is not None:
		for u in _vl:
			if u == 'ALL':
				continue

			print("*******************")
			val = g_users[u]

			print(val.q_ucalctime)
			tmp_list = [a/60. for a in val.q_ucalctime]
			val.q_ucalctime.clear()
			[val.q_ucalctime.append(b) for b in tmp_list]
			print(val.q_ucalctime)
			print(g_users[u].q_ucalctime)

	#cache.set('data_trend_tj', data_series_tj)
	#cache.set('data_trend_rj', data_series_rj)
	#cache.set('data_trend_fs', data_series_fs)
	#cache.set('data_trend_uct', data_series_uct)
	#cache.set('data_hist_jct', data_hist_jct)
	#cache.set('data_dist_jp', data_dist_jp)
	#cache.set('data_pie_tj', data_group_tj)
	#cache.set('data_pie_rj', data_group_rj)
	#cache.set('data_pie_qj', data_group_qj)

	cache.set("users_list", g_users)

	d = dict()
	d['farm'] = farm_id
	d['res'] = 0

	rnd = render(request, 'batch_monitor/update.html', d)
	return rnd