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

	if d['view_list'] is None:
		return HttpResponse("No data from farm")

	srs_tj = []
	srs_rj = []
	srs_fs = []
	srs_jp = []

	terms = dict()

	#cht_fs = Chart(
		#datasource = fair_share, 
		#series_options = 
		#[{'options':{
			#'type': 'line',
			#'stacking': False},
			#'terms': terms
			#}],
		#chart_options = 
		#{
			#'chart': {
				#'zoomType': 'x'},
			#'title': {
				#'text': 'Fair Share'},
			#'xAxis': {
				#'type': 'datetime',
				#'minRange': 10 * 60 * 1000,
				#'title': {
				#'text': 'Time'}},
			#'yAxis': {
				#'title': {
				#'text': 'Rank'}},
			#'plotOptions': {
				#'area': {
					##'fillColor': {
						##'linearGradient': { x1: 0, y1: 0, x2: 0, y2: 1},
						##'stops': [
							##[0, Highcharts.getOptions().colors[0]],
							##[1, Highcharts.Color(Highcharts.getOptions().colors[0]).setOpacity(0).get('rgba')]
						##]
					##},
					#'marker': {
						#'radius': 2
					#},
					#'lineWidth': 1,
					#'states': {
						#'hover': {
							#'lineWidth': 1
						#}
					#},
					#'threshold': 'null'
				#}
        #},
		#})

	#cht_jp = Chart(
		#datasource = job_progress, 
		#series_options = 
		#[{'options':{
			#'type': 'scatter'},
			#'terms': terms
			#}],
		#chart_options = 
		#{'title': {
			#'text': 'Jobs Race'},
		#'xAxis': {
				#'title': {
				#'text': 'Execution time [h]'}},
		#'yAxis': {
				#'title': {
				#'text': 'Progress [%]'}}
		#},
		##x_sortf_mapf_mts=(None, lambda i: datetime.fromtimestamp(i).strftime("%H:%M"), False)
		#)

	g_ts = cache.get("time_stamp", None)
	if g_ts is None:
		return HttpResponse("No ts on farm")

	g_users = cache.get("user_list", None)
	if g_users is None:
		return HttpResponse("No users on farm")

	_series_ts = list(g_ts.ts)
	_series_tj = []
	_series_rj = []
	_series_fs = []
	_series_jp = []

	for u in d['view_list']:
		val = g_users[u]

		_ltj = [list(a) for a in zip(_series_ts, list(val.q_njobsT))]
		_lrj = [list(a) for a in zip(_series_ts, list(val.q_njobsR))]

		_series_tj.append({ 'name' : u, 'data': _ltj })
		_series_rj.append({ 'name' : u, 'data': _lrj })

		if u != 'TOTAL':
			_lfs = [list(a) for a in zip(_series_ts, list(val.q_fairshare))]
			_series_fs.append({ 'name' : u, 'data': _lfs })
			_series_jp.append({ 'name' : u, 'data': list(val.l_jobprogress) })

	chart_tj = format_time_plot('Total jobs', xdata=_series_ts, ydata=_series_tj)
	chart_rj = format_time_plot('Running jobs', xdata=_series_ts, ydata=_series_rj)
	chart_fs = format_time_plot('Fair share', xdata=_series_ts, ydata=_series_fs)
	chart_jp = format_scatter_plot('Jobs race', xdata=_series_ts, ydata=_series_jp)

	#aaa = prepare_highcharts_data('line', 'Fair Share', 'time', 'fs', _series_ts, _series_tj)
	print(chart_tj)
	d['charts'] = [chart_tj, chart_rj, chart_fs, chart_jp]

	return render(request, 'batch_monitor/monitor.html', d)
	#return HttpResponse("Results %s " % poll_id)

def format_time_plot(title, xdata, ydata, xlabel='Time', ylabel='Jobs number'):
	chart = {
		'chart':{ 'type': 'line'},
		'title': {
			'text': title},
		'xAxis': {
			'allowDecimals' : 'false',
			'type': 'datetime',
			'title': { 'text': xlabel},
			'dateTimeLabelFormats' : {
				'hour' : '%H:%M',
				'day' : '%e. %b', }
			},
		'yAxis': {
				'title': { 'text': ylabel},
				},
		'series': ydata
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

	print(type(xdata))
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