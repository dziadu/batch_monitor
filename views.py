# Create your views here.

from django.core.cache import cache

from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404, render

from django.views import generic

from batch_monitor.models import BatchHostSettings

import batch_monitor.update

from chartit import DataPool, Chart

from datetime import datetime

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
	d['view_list'] = cache.get("view_list")

	srs_tj = []
	srs_rj = []
	srs_fs = []
	srs_jp = []

	terms = dict()

	_series_ts = []
	_series_tj = []
	_series_rj = []
	_series_fs = []
	_series_jp = []

	g_ts = cache.get("time_stamp", None)
	if g_ts is not None:
		_series_ts = list(g_ts.ts)

	g_users = cache.get("user_list", None)

	_vl = d['view_list']
	if _vl is not None:
		for u in _vl:
			if u == 'TOTAL':
				continue

			val = g_users[u]

			_ltj = [list(a) for a in zip(_series_ts, list(val.q_njobsT))]
			_lrj = [list(a) for a in zip(_series_ts, list(val.q_njobsR))]
			_lfs = [list(a) for a in zip(_series_ts, list(val.q_fairshare))]

			_series_tj.append({ 'name' : u, 'data': _ltj })
			_series_rj.append({ 'name' : u, 'data': _lrj })
			_series_fs.append({ 'name' : u, 'data': _lfs })
			_series_jp.append({ 'name' : u, 'data': list(val.l_jobprogress) })

		for u in _vl:
			if u != 'TOTAL':
				continue

			val = g_users[u]

			_ltj = [list(a) for a in zip(_series_ts, list(val.q_njobsT))]
			_lrj = [list(a) for a in zip(_series_ts, list(val.q_njobsR))]

			_series_tj.append({ 'name' : u, 'data': _ltj, 'zIndex': 0 })
			_series_rj.append({ 'name' : u, 'data': _lrj, 'zIndex': 0 })

			break

	chart_tj = format_time_plot('Total jobs', xdata=_series_ts, ydata=_series_tj)
	chart_rj = format_time_plot('Running jobs', xdata=_series_ts, ydata=_series_rj)
	chart_fs = format_time_plot('Fair share', xdata=_series_ts, ydata=_series_fs)
	chart_jp = format_scatter_plot('Jobs race', xdata=_series_ts, ydata=_series_jp)

	d['charts'] = [chart_tj, chart_rj, chart_fs, chart_jp]

	return render(request, 'batch_monitor/monitor.html', d)

def format_time_plot(title, xdata, ydata, xlabel='Time', ylabel='Jobs number'):
	chart = {
		'chart':{
			'type': 'line',
			'zoomType': 'x' },
		'title': {
			'text': title },
		'xAxis': {
			'allowDecimals' : 'false',
			'type': 'datetime',
			'title': {
				'text': xlabel },
			'dateTimeLabelFormats' : {
				'hour' : '%H:%M',
				'day' : '%e. %b', } },
		'yAxis': {
			'title': { 'text': ylabel },
			'floor': 0,
			},
		'series': ydata,
		'rangeSelector' : {
			'buttons': [{
				'type': 'minute',
				'count': 60,
				'text': '1h'
			}, {
				'type': 'minute',
				'count': 180,
				'text': '3h'
			}, {
				'type': 'all',
				'text': 'All'
			}]
			}
		}

	return chart

def format_scatter_plot(title, xdata, ydata, xlabel='Requested time [min]', ylabel='Progress [%]'):
	chart = {
		'chart':{ 'type': 'scatter'},
		'title': {
			'text': title},
		'xAxis': {
			'allowDecimals' : 'false',
			'title': { 'text': xlabel},
			},
		'yAxis': {
				'title': { 'text': ylabel},
				},
		'series': ydata
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

def update(request, farm_id):
    farm = get_object_or_404(BatchHostSettings, id=farm_id)

    batch_monitor.update.parse_farm(farm)

    d = dict()
    d['farm'] = farm

    return render(request, 'batch_monitor/update.html', d)