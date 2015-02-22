# Create your views here.

from django.core.cache import cache

from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404, render

from django.views import generic

from batch_monitor.models import BatchHostSettings

import json
import batch_monitor.update

from chartit import DataPool, Chart

from datetime import datetime

from decorators import json_response

label_total_jobs = 'Total jobs'
label_running_jobs = 'Running jobs'
label_queued_jobs = 'Queued jobs'
label_holded_jobs = 'Holded jobs'
label_jobs_race = 'Jobs race'
label_fair_share = 'Fair share rank'

class IndexView(generic.ListView):
	template_name = 'batch_monitor/index.html'
	context_object_name = 'farms_list'
	#model = BatchHostSettings

	cache.set("foo", "bar")

	def get_queryset(self):
		""" Return the last five published polls."""
		return BatchHostSettings.objects.all()

def monitor(request, farm_id):
	farm = get_object_or_404(BatchHostSettings, id=farm_id)

	d = dict()
	d['farm'] = farm

	chart_tj = cache.get('f_data_tj', None)
	chart_rj = cache.get('f_data_rj', None)
	chart_fs = cache.get('f_data_fs', None)
	chart_jp = cache.get('f_data_jp', None)

	if chart_tj is None:
		prepare_data(farm_id)

	chart_tj = cache.get('f_data_tj', None)
	chart_rj = cache.get('f_data_rj', None)
	chart_fs = cache.get('f_data_fs', None)
	chart_jp = cache.get('f_data_jp', None)

	d['charts'] = [chart_tj, chart_rj, chart_fs, chart_jp]

	return render(request, 'batch_monitor/monitor.html', d)

@json_response
def jsonreq(request, farm_id, data_type):
	farm = get_object_or_404(BatchHostSettings, id=farm_id)

	g_ts = cache.get("time_stamp", None)

	if 'lastts' in request.REQUEST:
		try:
			last_ts = int(request.REQUEST['lastts'])
		except ValueError:
			last_ts = 0
	else:
		last_ts = 0

	if g_ts is None:
		return None

	if data_type == "tj":
		response_data = cache.get('data_tj', None)
	elif data_type == "rj":
		response_data = cache.get('data_rj', None)
	elif data_type == "fs":
		response_data = cache.get('data_fs', None)
	elif data_type == "jp":
		response_data = cache.get('data_jp', None)
		print(cache.get('data_qj', None))
		print(cache.get('data_hj', None))
		return {
			'result': response_data,
			#'result': [],
			'pie': [{
					'name' : label_queued_jobs,
					'data': cache.get('data_qj', None),
				},
				{
					'name' : label_holded_jobs,
					'data': cache.get('data_hj', None),
				}]
			}
	else:
		response_data = None

	if response_data is None:
		return None

	lt = int(last_ts)
	if lt == 0:
		return { 'full': g_ts.colsize, 'result': response_data }

	_data = response_data[0]['data']
	_len = len(_data)

	for i in reversed(xrange(_len)):
		if _data[i][0] <= lt:
			_response_data = response_data
			for j in xrange(len(response_data)):
				_response_data[j]['data'] = response_data[j]['data'][i+1:_len]
			return { 'limit': g_ts.colsize, 'result': _response_data }

	return None

def update(request, farm_id):
	farm = get_object_or_404(BatchHostSettings, id=farm_id)

	batch_monitor.update.parse_farm(farm)

	d = dict()
	d['farm'] = farm

	prepare_data(farm_id)

	return render(request, 'batch_monitor/update.html', d)

def prepare_data(farm):
	data_list_ts = []
	data_series_tj = []
	data_series_rj = []
	data_group_qj = []
	data_group_hj = []

	data_series_fs = []
	data_group_jp = []

	g_ts = cache.get("time_stamp", None)

	if g_ts is not None:
		data_list_ts = list(g_ts.ts)

	g_users = cache.get("user_list", None)

	total_queued = 0
	total_holded = 0

	_vl = cache.get('view_list', None)
	if _vl is not None:
		for u in _vl:
			if u == 'ALL':
				continue

			val = g_users[u]
			idx = g_users.keys().index(u)

			_ltj = [list(a) for a in zip(data_list_ts, list(val.q_njobsT))]
			_lrj = [list(a) for a in zip(data_list_ts, list(val.q_njobsR))]

			_n_qj = val.q_njobsQ[len(val.q_njobsQ)-1]
			_n_hj = val.q_njobsH[len(val.q_njobsH)-1]

			total_queued += _n_qj
			total_holded += _n_hj

			_lfs = [list(a) for a in zip(data_list_ts, list(val.q_fairshare))]

			data_series_tj.append({ 'name' : val.name, 'data': _ltj, 'index': idx })
			data_series_rj.append({ 'name' : val.name, 'data': _lrj, 'index': idx })

			col_idx = len(data_series_tj)-1
			if _n_qj > 0:
				data_group_qj.append({ 'name' : val.name, 'y': _n_qj, '_color': col_idx })

			if _n_hj > 0:
				data_group_hj.append({ 'name' : val.name, 'y': _n_hj, '_color': col_idx })

			data_series_fs.append({ 'name' : val.name, 'data': _lfs, 'index': idx })
			
			data_group_jp.append({ 'name' : val.name, 'data': list(val.l_jobprogress), 'index': idx })

		for u in _vl:
			if u != 'ALL':
				continue

			val = g_users[u]

			_ltj = [list(a) for a in zip(data_list_ts, list(val.q_njobsT))]
			_lrj = [list(a) for a in zip(data_list_ts, list(val.q_njobsR))]

			data_series_tj.append({ 'name' : val.name, 'data': _ltj, 'zIndex': -1, 'index': 99999 })
			data_series_rj.append({ 'name' : val.name, 'data': _lrj, 'zIndex': -1, 'index': 99999 })

			break

	chart_tj = format_time_plot(farm, 'tj', label_total_jobs, series_data=data_series_tj)
	chart_rj = format_time_plot(farm, 'rj', label_running_jobs, series_data=data_series_rj)
	chart_fs = format_time_plot(farm, 'fs', label_fair_share, series_data=data_series_fs)

	print(data_group_qj)
	if total_queued > 0:
		pie_chart_qj = format_pie_chart(label_queued_jobs, data_group_qj, [ '30%', '50%' ])
	else:
		pie_chart_qj = None

	print(data_group_hj)
	if total_holded > 0:
		pie_chart_hj = format_pie_chart(label_holded_jobs, data_group_hj, [ '70%', '50%' ])
	else:
		pie_chart_hj = None

	if pie_chart_qj is None and pie_chart_hj is None:
		scatter_pie_all_data = data_group_jp
	elif pie_chart_qj is None:
		scatter_pie_all_data = data_group_jp + [pie_chart_hj,]
	elif pie_chart_hj is None:
		scatter_pie_all_data = data_group_jp + [pie_chart_qj,]
	else:
		scatter_pie_all_data = data_group_jp + [ pie_chart_qj, pie_chart_hj]

	chart_jp = format_scatter_plot(farm, 'jp', label_jobs_race, data=scatter_pie_all_data)

	cache.set('data_tj', data_series_tj)
	cache.set('data_rj', data_series_rj)
	cache.set('data_qj', data_group_qj)
	cache.set('data_hj', data_group_hj)
	cache.set('data_fs', data_series_fs)
	cache.set('data_jp', data_group_jp)

	cache.set('f_data_tj', chart_tj)
	cache.set('f_data_rj', chart_rj)
	cache.set('f_data_fs', chart_fs)
	cache.set('f_data_jp', chart_jp)

def format_time_plot(farm, chart_type, title, series_data, xlabel='Time', ylabel='Jobs number'):
	chart = {
		'chart':{
			'type': 'line',
			'zoomType': 'x',
			'events': {
				'load': "$@#function() {"
					" time_chart_updater(" + farm + ", this, '" + chart_type + "');"
					" }#@$"
					, } },
		'title': {
			'text': title },
		'subtitle': {
			'text': ' -- ' },
		'xAxis': {
			'allowDecimals' : 'false',
			'type': 'datetime',
			'title': {
				'text': xlabel },
			'dateTimeLabelFormats' : {
				'hour' : '%H:%M',
				'day' : '%e. %b', }, },
		'yAxis': {
			'title': { 'text': ylabel },
			'floor': 0,
			},
		'series': series_data
		}

	return chart

def format_scatter_plot(farm, chart_type, title, data=[], xlabel='Requested time [min]', ylabel='Progress [%]'):
	chart = {
		'chart':{
			'type': 'scatter',
			'events': {
				'load':
					"$@#function() {"
					" scatter_chart_updater(" + farm + ", this, '" + chart_type + "');"
					" }#@$"
			}
		},
		'title': {
			'text': title
		},
		'subtitle': {
			'text': ' -- '
		},
		'xAxis': {
			'allowDecimals' : 'false',
			'title': { 'text': xlabel},
		},
		'yAxis': {
			'title': { 'text': ylabel},
			'floor': 0,
			'ceiling': 1,
		},
		'series': data,
		'plotOptions': {
			'pie': {
				'allowPointSelect': True,
				'cursor': 'pointer',
				'dataLabels': {
					'enabled': True,
					'format': '<b>{point.name}</b>: {point.y}',
					'style': {
						'color': 'black'
					},
					'connectorColor': 'silver'
				}
			}
		}
	}
	return chart

def format_pie_chart(title, pie_data, center, size='50%'):
	chart = {
		'type': 'pie',
		'name': title,
		'data': pie_data,
		'center': center,
		'size': size,
		'showInLegend': False,
		'dataLabels': {
			'enabled': True
		}
	}
	return chart