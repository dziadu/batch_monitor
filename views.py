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

class IndexView(generic.ListView):
    template_name = 'batch_monitor/index.html'
    context_object_name = 'farms_list'
    #model = BatchHostSettings

    cache.set("foo", "bar")

    def get_queryset(self):
        """ Return the last five published polls."""
        return BatchHostSettings.objects.order_by('-name')[:5]

def monitor(request, farm_id):
	farm = get_object_or_404(BatchHostSettings, id=farm_id)

	d = dict()
	d['farm'] = farm

	chart_tj = cache.get('f_data_tj', None)
	chart_rj = cache.get('f_data_rj', None)
	chart_fs = cache.get('f_data_fs', None)
	chart_jp = cache.get('f_data_jp', None)

	if chart_tj is None:
		prepare_data()

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
		return { 'result': response_data }
	else:
		response_data = None

	if response_data is None:
		return None

	lt = int(last_ts)
	if lt == 0:
		return { 'full': g_ts.colsize, 'result': response_data }

	_data = response_data[0]['data']
	_len = len(_data)

	for i in xrange(_len):
		if _data[i][0] > lt:
			_response_data = response_data
			for j in xrange(len(response_data)):
				_response_data[j]['data'] = response_data[j]['data'][i:_len]
			return { 'limit': g_ts.colsize, 'result': _response_data }

	return None

def update(request, farm_id):
	farm = get_object_or_404(BatchHostSettings, id=farm_id)

	batch_monitor.update.parse_farm(farm)

	d = dict()
	d['farm'] = farm

	prepare_data()

	return render(request, 'batch_monitor/update.html', d)

def prepare_data():
	_series_ts = []
	_series_tj = []
	_series_rj = []
	_series_fs = []
	_series_jp = []

	g_ts = cache.get("time_stamp", None)

	if g_ts is not None:
		_series_ts = list(g_ts.ts)

	g_users = cache.get("user_list", None)

	_vl = cache.get('view_list', None)
	if _vl is not None:
		for u in _vl:
			if u == 'ALL':
				continue

			val = g_users[u]

			_ltj = [list(a) for a in zip(_series_ts, list(val.q_njobsT))]
			_lrj = [list(a) for a in zip(_series_ts, list(val.q_njobsR))]
			_lfs = [list(a) for a in zip(_series_ts, list(val.q_fairshare))]

			_series_tj.append({ 'name' : val.name, 'data': _ltj })
			_series_rj.append({ 'name' : val.name, 'data': _lrj })
			_series_fs.append({ 'name' : val.name, 'data': _lfs })
			_series_jp.append({ 'name' : val.name, 'data': list(val.l_jobprogress) })

		for u in _vl:
			if u != 'ALL':
				continue

			val = g_users[u]

			_ltj = [list(a) for a in zip(_series_ts, list(val.q_njobsT))]
			_lrj = [list(a) for a in zip(_series_ts, list(val.q_njobsR))]

			_series_tj.append({ 'name' : val.name, 'data': _ltj, 'zIndex': -1 })
			_series_rj.append({ 'name' : val.name, 'data': _lrj, 'zIndex': -1 })

			break

	chart_tj = format_time_plot('tj', 'Total jobs', xdata=_series_ts, ydata=_series_tj)
	chart_rj = format_time_plot('rj', 'Running jobs', xdata=_series_ts, ydata=_series_rj)
	chart_fs = format_time_plot('fs', 'Fair share', xdata=_series_ts, ydata=_series_fs)
	chart_jp = format_scatter_plot('jp', 'Jobs race', xdata=_series_ts, ydata=_series_jp)

	cache.set('data_tj', _series_tj)
	cache.set('data_rj', _series_rj)
	cache.set('data_fs', _series_fs)
	cache.set('data_jp', _series_jp)

	cache.set('f_data_tj', chart_tj)
	cache.set('f_data_rj', chart_rj)
	cache.set('f_data_fs', chart_fs)
	cache.set('f_data_jp', chart_jp)

def format_time_plot(chart_type, title, xdata, ydata, xlabel='Time', ylabel='Jobs number'):
	chart = {
		'chart':{
			'type': 'line',
			'zoomType': 'x',
			'events': {
				'load': "$@#function() { time_chart_updater(this, '" + chart_type + "')}#@$", }, },
		'title': {
			'text': title },
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
		#'series': ydata
		}

	return chart

def format_scatter_plot(chart_type, title, xdata, ydata, xlabel='Requested time [min]', ylabel='Progress [%]'):
	chart = {
		'chart':{
			'type': 'scatter',
			'events': {
				'load': "$@#function() { scatter_chart_updater(this, '" + chart_type + "')}#@$", }, },
		'title': {
			'text': title},
		'xAxis': {
			'allowDecimals' : 'false',
			'title': { 'text': xlabel},
			},
		'yAxis': {
				'title': { 'text': ylabel},
				'floor': 0,
				},
		#'series': ydata
		}
	return chart

def prepare_highcharts_data(chart, title, xaxis, yaxis, xdata, ydata, aux=None):
	result = {}

	if type(chart) is dict():
		result['chart'] = chart
	else:
		_var = { 'type': chart}
		result['chart'] = _var

	if type(title) is dict():
		result['title'] = title
	else:
		_var = { 'text': title}
		result['title'] = _var

	if type(xaxis) is dict():
		result['xAxis'] = xaxis
	else:
		_var = { 'title': { 'text': xaxis} }
		result['xAxis'] = _var

	if type(yaxis) is dict():
		result['yAxis'] = yaxis
	else:
		_var = { 'title': { 'text': yaxis} }
		result['yAxis'] = _var

	if type(xdata) is list:
		result['xAxis']['collection'] = xdata

	_series = ydata
	result['series'] = _series

	return result