# Create your views here.

from django.core.cache import cache

from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, render

from django.views import generic

from batch_monitor.models import BatchHostSettings

import json
import batch_monitor.update

from chartit import DataPool, Chart

from datetime import datetime

from decorators import json_response

label_tj = 'Total jobs'
label_rj = 'Running jobs'
label_qj = 'Queued jobs'
label_hj = 'Hold jobs'
label_jp = 'Jobs race'
label_fs = 'Fair share rank'
label_jct = 'Jobs computing time'

class IndexView(generic.ListView):
	template_name = 'batch_monitor/index.html'
	context_object_name = 'farms_list'
	#model = BatchHostSettings

	def get_queryset(self):
		""" Return the last five published polls."""
		return BatchHostSettings.objects.all()

#views 
def update(request, farm_id):
	farm = get_object_or_404(BatchHostSettings, id=farm_id)

	d = dict()
	d['farm'] = farm
	d['res'] = 0

	#lock = cache.get("lock", False)

	#if lock:
		#d['res'] = 1
		#return HttpResponseForbidden(render(request, 'batch_monitor/update.html', d))

	#lock = True
	#cache.set("lock", lock)

	if batch_monitor.update.parse_farm(farm):
		prepare_data(farm_id)
	else:
		d['res'] = 2
		return HttpResponseForbidden(render(request, 'batch_monitor/update.html', d))

	rnd = render(request, 'batch_monitor/update.html', d)

	#lock = False
	#cache.set("lock", lock)

	return rnd

def monitor(request, farm_id):
	farm = get_object_or_404(BatchHostSettings, id=farm_id)
	d = dict()
	d['farm'] = farm
	data_series_tj = cache.get('data_tj', None)

	if data_series_tj is None:
		prepare_data(farm_id)

	data_series_tj = cache.get('data_tj', None)
	data_series_rj = cache.get('data_rj', None)
	data_group_qj = cache.get('data_qj_f', None)
	data_group_hj = cache.get('data_hj_f', None)
	data_series_fs = cache.get('data_fs', None)
	data_group_jp = cache.get('data_jp', None)
	data_series_jct = cache.get('data_jct', None)

	chart_tj = format_time_plot(farm_id, 'tj', label_tj, series_data=data_series_tj)
	chart_rj = format_time_plot(farm_id, 'rj', label_rj, series_data=data_series_rj)
	chart_fs = format_time_plot(farm_id, 'fs', label_fs, series_data=data_series_fs)
	chart_jct = format_hist_plot(farm_id, 'jct', label_jct, series_data=data_series_jct)

	pie_chart_qj = format_pie_chart(label_qj, data_group_qj, [ '30%', '50%' ])
	pie_chart_hj = format_pie_chart(label_hj, data_group_hj, [ '70%', '50%' ])

	scatter_pie_all_data = data_group_jp + [ pie_chart_qj, pie_chart_hj]

	chart_jp = format_scatter_plot(farm_id, 'jp', label_jp, data=scatter_pie_all_data)

	d['charts'] = [chart_tj, chart_rj, chart_fs, chart_jp, chart_jct]

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
		return {
			'result': response_data,
			'pie': [{
					'name' : label_qj,
					'data': cache.get('data_qj', None),
				},
				{
					'name' : label_hj,
					'data': cache.get('data_hj', None),
				}]
			}
	elif data_type == "jct":
		response_data = cache.get('data_jct', None)

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

# tools
def prepare_data(farm):
	data_list_ts = []
	data_series_tj = []
	data_series_rj = []
	data_group_qj = []
	data_group_hj = []

	data_series_fs = []
	data_group_jp = []

	data_series_jct = []

	g_ts = cache.get("time_stamp", None)

	if g_ts is not None:
		data_list_ts = list(g_ts.ts)

	g_users = cache.get("users_list", None)

	_vl = cache.get("views_list", None)
	if _vl is not None:
		for u in _vl:
			if u == 'ALL':
				continue

			val = g_users[u]
			idx = g_users.keys().index(u)
			col_idx = len(data_series_tj)

			_ltj = [list(a) for a in zip(data_list_ts, list(val.q_njobsT))]
			_lrj = [list(a) for a in zip(data_list_ts, list(val.q_njobsR))]

			_n_qj = val.q_njobsQ[len(val.q_njobsQ)-1]
			_n_hj = val.q_njobsH[len(val.q_njobsH)-1]

			_lfs = [list(a) for a in zip(data_list_ts, list(val.q_fairshare))]
			_ljp = list(val.l_jobprogress)
			
			_ljct = histogramize(val.q_calctime, 20, 0, 120)

			data_series_tj.append({ 'name' : val.name, 'data': _ltj, 'zIndex': col_idx, 'index': idx, '_color': col_idx })
			data_series_rj.append({ 'name' : val.name, 'data': _lrj, 'zIndex': col_idx, 'index': idx, '_color': col_idx })
			data_series_fs.append({ 'name' : val.name, 'data': _lfs, 'zIndex': col_idx, 'index': idx, '_color': col_idx })
			data_group_jp.append({ 'name' : val.name, 'data': _ljp, 'zIndex': col_idx, 'index': idx, '_color': col_idx })

			if _n_qj > 0:
				data_group_qj.append({ 'name' : val.name, 'y': _n_qj, '_color': col_idx })
			if _n_hj > 0:
				data_group_hj.append({ 'name' : val.name, 'y': _n_hj, '_color': col_idx })

			data_series_jct.append({ 'name' : val.name, 'data': _ljct, 'zIndex': col_idx, 'index': idx, '_color': col_idx })


		val = g_users['ALL']
		col_idx = len(data_series_tj)

		_ltj = [list(a) for a in zip(data_list_ts, list(val.q_njobsT))]
		_lrj = [list(a) for a in zip(data_list_ts, list(val.q_njobsR))]

		data_series_tj.append({ 'name' : val.name, 'data': _ltj, 'zIndex': -1, 'index': 99999, '_color': col_idx })
		data_series_rj.append({ 'name' : val.name, 'data': _lrj, 'zIndex': -1, 'index': 99999, '_color': col_idx })

	cache.set('data_tj', data_series_tj)
	cache.set('data_rj', data_series_rj)
	cache.set('data_qj', data_group_qj)
	cache.set('data_hj', data_group_hj)
	cache.set('data_fs', data_series_fs)
	cache.set('data_jp', data_group_jp)
	cache.set('data_jct', data_series_jct)

	for i in xrange(len(data_group_qj)):
		_c = data_group_qj[i]['_color']
		data_group_qj[i]['color'] = '$@#Highcharts.getOptions().colors[ %d ]#@$' % _c

	for i in xrange(len(data_group_hj)):
		_c = data_group_hj[i]['_color']
		data_group_hj[i]['color'] = '$@#Highcharts.getOptions().colors[ %d ]#@$' % _c

	cache.set('data_qj_f', data_group_qj)
	cache.set('data_hj_f', data_group_hj)

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
		'series': series_data,
		}

	return chart

def format_hist_plot(farm, chart_type, title, series_data, xlabel='Time', ylabel='Jobs number'):
	chart = {
		'chart':{
			'type': 'line',
			'zoomType': 'x',
			'events': {
				'load': "$@#function() {"
					" hist_chart_updater(" + farm + ", this, '" + chart_type + "');"
					" }#@$"
					, } },
		'title': {
			'text': title },
		'subtitle': {
			'text': ' -- ' },
		'xAxis': {
			'allowDecimals' : 'false',
			'title': {
				'text': xlabel }, },
		'yAxis': {
			'title': { 'text': ylabel },
			'floor': 0,
			},
		'series': series_data,
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


def histogramize(data, bins, bmin, bmax):
	tick = float(bmax - bmin)/bins
	histo = [None] * bins

	for i in xrange(bins):
		histo[i] = [ bmin + i*tick + tick/2, 0 ]

	for i in xrange(len(data)):
		val = float(data[i])
		_bin = int( (val - bmin) / tick )
		if _bin >= 0 and _bin < bins:
			histo[_bin][1] += 1

	return histo