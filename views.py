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
	data_series_tj = cache.get('data_ser_tj', None)

	if data_series_tj is None:
		prepare_data(farm_id)

	data_series_tj = cache.get('data_ser_tj', None)
	data_series_rj = cache.get('data_ser_rj', None)
	data_group_rj = cache.get('data_rj_f', None)
	data_group_qj = cache.get('data_qj_f', None)
	data_group_hj = cache.get('data_hj_f', None)
	data_series_fs = cache.get('data_fs', None)
	data_group_jp = cache.get('data_jp', None)
	data_series_jct = cache.get('data_jct', None)

	chart_tj = format_time_plot(farm_id, 'tj', label_tj, series_data=data_series_tj)
	chart_rj = format_time_plot(farm_id, 'rj', label_rj, series_data=data_series_rj)
	chart_fs = format_time_plot(farm_id, 'fs', label_fs, series_data=data_series_fs)
	chart_jct = format_hist_plot(farm_id, 'jct', label_jct, series_data=data_series_jct)

	pie_chart_rj = format_embedded_pie_chart(label_rj, data_group_rj, [ '17%', '50%' ])
	pie_chart_qj = format_embedded_pie_chart(label_qj, data_group_qj, [ '50%', '50%' ])
	pie_chart_hj = format_embedded_pie_chart(label_hj, data_group_hj, [ '83%', '50%' ])

	scatter_pie_all_data = data_group_jp + [ pie_chart_qj, pie_chart_hj]
	embedded_pie_all = [ pie_chart_rj, pie_chart_qj, pie_chart_hj]

	chart_jp = format_scatter_plot(farm_id, 'jp', label_jp, data=scatter_pie_all_data)
	chart_js = format_pie_chart(farm_id, 'js', 'Jobs summary', data=embedded_pie_all)

	d['charts'] = [chart_tj, chart_rj, chart_fs, chart_jp, chart_jct, chart_js]

	return render(request, 'batch_monitor/monitor.html', d)

# tools
def prepare_data(farm):
	data_list_ts = []
	data_series_tj = []
	data_series_rj = []
	data_group_rj = []
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

			_n_rj = val.q_njobsR[len(val.q_njobsR)-1]
			_n_qj = val.q_njobsQ[len(val.q_njobsQ)-1]
			_n_hj = val.q_njobsH[len(val.q_njobsH)-1]

			_lfs = [list(a) for a in zip(data_list_ts, list(val.q_fairshare))]
			_ljp = list(val.l_jobprogress)
			
			_ljct = histogramize(val.q_calctime, 24, 0, 120)

			data_series_tj.append({ 'name' : val.name, 'data': _ltj, 'zIndex': col_idx, 'index': idx, '_color': col_idx })
			data_series_rj.append({ 'name' : val.name, 'data': _lrj, 'zIndex': col_idx, 'index': idx, '_color': col_idx })
			data_series_fs.append({ 'name' : val.name, 'data': _lfs, 'zIndex': col_idx, 'index': idx, '_color': col_idx })
			data_group_jp.append({ 'name' : val.name, 'data': _ljp, 'zIndex': col_idx, 'index': idx, '_color': col_idx })

			if _n_rj > 0:
				data_group_rj.append({ 'name' : val.name, 'y': _n_rj, '_color': col_idx })
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

	cache.set('data_ser_tj', data_series_tj)
	cache.set('data_ser_rj', data_series_rj)
	cache.set('data_pie_rj', data_group_rj)
	cache.set('data_pie_qj', data_group_qj)
	cache.set('data_pie_hj', data_group_hj)
	cache.set('data_ser_fs', data_series_fs)
	cache.set('data_jp', data_group_jp)
	cache.set('data_jct', data_series_jct)

	for i in xrange(len(data_group_rj)):
		_c = data_group_rj[i]['_color']
		data_group_rj[i]['color'] = '$@#Highcharts.getOptions().colors[ %d ]#@$' % _c

	for i in xrange(len(data_group_qj)):
		_c = data_group_qj[i]['_color']
		data_group_qj[i]['color'] = '$@#Highcharts.getOptions().colors[ %d ]#@$' % _c

	for i in xrange(len(data_group_hj)):
		_c = data_group_hj[i]['_color']
		data_group_hj[i]['color'] = '$@#Highcharts.getOptions().colors[ %d ]#@$' % _c

	cache.set('data_rj_f', data_group_rj)
	cache.set('data_qj_f', data_group_qj)
	cache.set('data_hj_f', data_group_hj)

def format_time_plot(farm, chart_data_type, title, series_data, xlabel='Time', ylabel='Jobs number'):
	chart = {
		'chart':{
			'type': 'line',
			'zoomType': 'x',
			'events': {
				'load': "$@#function() {"
					" time_chart_updater(" + farm + ", this, '" + chart_data_type + "');"
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

def format_hist_plot(farm, chart_data_type, title, series_data, xlabel='Time', ylabel='Jobs number'):
	chart = {
		'chart':{
			'type': 'line',
			'zoomType': 'x',
			'events': {
				'load': "$@#function() {"
					" hist_chart_updater(" + farm + ", this, '" + chart_data_type + "');"
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

def format_scatter_plot(farm, chart_data_type, title, data=[], xlabel='Requested time [min]', ylabel='Progress [%]'):
	chart = {
		'chart':{
			'type': 'scatter',
			'events': {
				'load':
					"$@#function() {"
					" scatter_chart_updater(" + farm + ", this, '" + chart_data_type + "');"
					" }#@$"
			},
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

def format_pie_chart(farm, chart_data_type, title, data=[]):
	chart = {
		'chart':{
			'type': 'pie',
			'events': {
				'load':
					"$@#function() {"
					" pie_chart_updater(" + farm + ", this, '" + chart_data_type + "');"
					" }#@$"
			}
		},
		'title': {
			'text': title
		},
		'subtitle': {
			'text': ' -- '
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

def format_embedded_pie_chart(title, pie_data, center, size='40%'):
	chart = {
		'type': 'pie',
		'name': title,
		'data': pie_data,
		'center': center,
		'size': size,
		'showInLegend': False,
		'dataLabels': {
			'enabled': True
		},
		'labels': {
			'items': [{
				'html': 'Running jobssss',
			}]
		},
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