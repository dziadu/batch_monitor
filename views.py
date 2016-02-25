# Create your views here.

from django.core.cache import cache
from django.conf import settings

from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, render

from django.views import generic

from batch_monitor.models import BatchHostSettings

import json
import batch_monitor.update

from chartit import DataPool, Chart

from datetime import datetime

from batch_monitor.conf import config as bmconfig

label_tj = 'Total jobs'
label_rj = 'Running jobs'
label_qj = 'Queued jobs'
label_hj = 'Hold jobs'
label_jp = 'Jobs race'
label_fs = 'Fair share rank'
label_jct = 'Jobs computing time'
label_uct = 'Users computing time'

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
	data_series_tj = cache.get('data_trend_tj', None)

	if data_series_tj is None:
		prepare_data(farm_id)

	if hasattr(settings, 'BATCH_FARM_SEND_INITIAL_DATA') and settings.BATCH_FARM_SEND_INITIAL_DATA == True:
		data_series_tj = cache.get('data_trend_tj', [])
		data_series_rj = cache.get('data_trend_rj', [])
		data_series_fs = cache.get('data_trend_fs', [])
		data_series_uct = cache.get('data_trend_uct', [])
		data_hist_jct = cache.get('data_hist_jct', [])
		data_dist_jp = cache.get('data_dist_jp', [])
		data_group_tj = cache.get('data_tj_f', [])
		data_group_rj = cache.get('data_rj_f', [])
		data_group_qj = cache.get('data_qj_f', [])
	else:
		data_series_tj = []
		data_series_rj = []
		data_series_fs = []
		data_series_uct = []
		data_hist_jct = []
		data_dist_jp = []
		data_group_tj = []
		data_group_rj = []
		data_group_qj = []

	chart_tj = format_trend_plot(farm_id, 'tj', label_tj, series_data=data_series_tj)
	chart_rj = format_trend_plot(farm_id, 'rj', label_rj, series_data=data_series_rj)
	chart_fs = format_trend_plot(farm_id, 'fs', label_fs, series_data=data_series_fs)
	chart_uct = format_trend_plot(farm_id, 'uct', label_uct, series_data=data_series_uct, ylabel='Time [min]')

	chart_jct = format_hist_plot(farm_id, 'jct', label_jct, series_data=data_hist_jct)

	pie_chart_tj = format_embedded_pie_chart(label_tj, data_group_tj, [ '17%', '50%' ])
	pie_chart_rj = format_embedded_pie_chart(label_rj, data_group_rj, [ '50%', '50%' ])
	pie_chart_qj = format_embedded_pie_chart(label_qj, data_group_qj, [ '83%', '50%' ])

	scatter_pie_all_data = data_dist_jp
	embedded_pie_all = [ pie_chart_tj, pie_chart_rj, pie_chart_qj]

	chart_jp = format_dist_plot(farm_id, 'jp', label_jp, data=scatter_pie_all_data)
	chart_js = format_pie_chart(farm_id, 'js', 'Jobs summary', data=embedded_pie_all)

	d['charts'] = [chart_tj, chart_rj, chart_fs, chart_jp, chart_jct, chart_uct, chart_js]

	return render(request, 'batch_monitor/monitor.html', d)

# tools
def prepare_data(farm):
	data_list_ts = []

	data_series_tj = []
	data_series_rj = []
	data_series_fs = []
	data_series_uct = []

	data_hist_jct = []
	data_dist_jp = []

	data_group_tj = []
	data_group_rj = []
	data_group_qj = []

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

			_ltj = [list(a) for a in zip(data_list_ts[-len(val.q_njobsT):], list(val.q_njobsT))]
			_lrj = [list(a) for a in zip(data_list_ts[-len(val.q_njobsR):], list(val.q_njobsR))]

			_n_tj = val.q_njobsT[len(val.q_njobsT)-1]
			_n_rj = val.q_njobsR[len(val.q_njobsR)-1]
			_n_qj = val.q_njobsQ[len(val.q_njobsQ)-1]

			_lfs = [list(a) for a in zip(data_list_ts[-len(val.q_fairshare):], list(val.q_fairshare))]
			_ljp = list(val.l_jobprogress)

			_ljct = histogramize(val.q_jcalctime, 24, 0, 120)
			_luct = [list(a) for a in zip(data_list_ts[-len(val.q_ucalctime):], list(val.q_ucalctime))]

			user_name = val.name
			if bmconfig.user_map is not None:
				if user_name in bmconfig.user_map:
					user_name = bmconfig.user_map[user_name]

			data_series_tj.append({ 'name' : user_name, 'data': _ltj, 'zIndex': col_idx, 'index': idx, '_color': col_idx })
			data_series_rj.append({ 'name' : user_name, 'data': _lrj, 'zIndex': col_idx, 'index': idx, '_color': col_idx })
			data_series_fs.append({ 'name' : user_name, 'data': _lfs, 'zIndex': col_idx, 'index': idx, '_color': col_idx })
			data_series_uct.append({ 'name' : user_name, 'data': _luct, 'zIndex': col_idx, 'index': idx, '_color': col_idx })

			data_dist_jp.append({ 'name' : user_name, 'data': _ljp, 'zIndex': col_idx, 'index': idx, '_color': col_idx })

			if _n_tj > 0:
				data_group_tj.append({ 'name' : user_name, 'y': _n_tj, '_color': col_idx })
			if _n_rj > 0:
				data_group_rj.append({ 'name' : user_name, 'y': _n_rj, '_color': col_idx })
			if _n_qj > 0:
				data_group_qj.append({ 'name' : user_name, 'y': _n_qj, '_color': col_idx })

			data_hist_jct.append({ 'name' : user_name, 'data': _ljct, 'zIndex': col_idx, 'index': idx, '_color': col_idx })


		val = g_users['ALL']
		col_idx = len(data_series_tj)

		_ltj = [list(a) for a in zip(data_list_ts, list(val.q_njobsT))]
		_lrj = [list(a) for a in zip(data_list_ts, list(val.q_njobsR))]

		data_series_tj.append({ 'name' : user_name, 'data': _ltj, 'zIndex': -1, 'index': 99999, '_color': col_idx })
		data_series_rj.append({ 'name' : user_name, 'data': _lrj, 'zIndex': -1, 'index': 99999, '_color': col_idx })

	cache.set('data_trend_tj', data_series_tj)
	cache.set('data_trend_rj', data_series_rj)
	cache.set('data_trend_fs', data_series_fs)
	cache.set('data_trend_uct', data_series_uct)
	cache.set('data_hist_jct', data_hist_jct)
	cache.set('data_dist_jp', data_dist_jp)
	cache.set('data_pie_tj', data_group_tj)
	cache.set('data_pie_rj', data_group_rj)
	cache.set('data_pie_qj', data_group_qj)

	for i in xrange(len(data_group_tj)):
		_c = data_group_tj[i]['_color']
		data_group_tj[i]['color'] = '$@#Highcharts.getOptions().colors[ %d ]#@$' % _c

	for i in xrange(len(data_group_rj)):
		_c = data_group_rj[i]['_color']
		data_group_rj[i]['color'] = '$@#Highcharts.getOptions().colors[ %d ]#@$' % _c

	for i in xrange(len(data_group_qj)):
		_c = data_group_qj[i]['_color']
		data_group_qj[i]['color'] = '$@#Highcharts.getOptions().colors[ %d ]#@$' % _c

	cache.set('data_tj_f', data_group_tj)
	cache.set('data_rj_f', data_group_rj)
	cache.set('data_qj_f', data_group_qj)

def format_trend_plot(farm, chart_data_type, title, series_data, xlabel='Time', ylabel='Jobs number'):
	chart = {
		'chart':{
			'reflow': False,
			'type': 'line',
			'zoomType': 'x',
			'events': {
				'load': "$@#function() {"
					" time_chart_updater(" + farm + ", this, '" + chart_data_type + "');"
					" }#@$",
				}
			},
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
			'floor': 0,
			'ceiling' : 130,
			'title': { 'text': ylabel },
			},
		'series': series_data,
		}

	return chart

def format_hist_plot(farm, chart_data_type, title, series_data, xlabel='Time [min]', ylabel='Jobs number'):
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

def format_dist_plot(farm, chart_data_type, title, data=[], xlabel='Requested time [min]', ylabel='Progress [%]'):
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
			'ceiling': 105,
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
					" }#@$",
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

def format_embedded_pie_chart(title, pie_data, center, size='50%'):
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
	}
	return chart

def histogramize(data, bins, bmin, bmax):
	tick = float(bmax - bmin)/bins
	histo = [None] * bins

	for i in xrange(bins):
		histo[i] = [ bmin + i*tick + tick/2, None ]

	for i in xrange(len(data)):
		val = float(data[i])
		_bin = int( (val - bmin) / tick )
		if _bin >= 0 and _bin < bins:
			histo[_bin][1] = int(histo[_bin][1] or 0) + 1

	return histo
