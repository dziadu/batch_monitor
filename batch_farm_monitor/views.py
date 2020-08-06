# Create your views here.

from django.core.cache import cache
from django.conf import settings
from django.urls import *

from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, render

from django.views import generic

from django.templatetags.static import static

import os

from batch_farm_monitor.models import BatchHostSettings
import batch_farm_monitor

import json
import batch_farm_monitor.update

from chartit import DataPool, Chart

from datetime import datetime

from batch_farm_monitor.conf import config as bmconfig

label_submitted = 'Submitted jobs'
label_running = 'Running jobs'
label_queued = 'Queued jobs'
label_hold = 'Hold jobs'
label_progress = 'Jobs race'
label_fairshare = 'Fair share rank'
label_jcomptime = 'Jobs computing time'
label_ucomptime = 'Users computing time'

class IndexView(generic.ListView):
    template_name = 'batch_farm_monitor/index.html'
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
        #return HttpResponseForbidden(render(request, 'batch_farm_monitor/update.html', d))

    #lock = True
    #cache.set("lock", lock)

    if batch_farm_monitor.update.parse_farm(farm):
        prepare_data(farm_id)
    else:
        d['res'] = 2
        return HttpResponseForbidden(render(request, 'batch_farm_monitor/update.html', d))

    d['farm_out'] = cache.get('farm_out', "EMPTY")
    rnd = render(request, 'batch_farm_monitor/update.html', d)

    #lock = False
    #cache.set("lock", lock)

    return rnd

def monitor(request, farm_id):
    farm = get_object_or_404(BatchHostSettings, id=farm_id)
    d = dict()
    d['farm'] = farm
    data_series_submitted = cache.get('trend_submitted', None)

    if data_series_submitted is None:
        prepare_data(farm_id)

    if hasattr(settings, 'BATCH_FARM_SEND_INITIAL_DATA') and settings.BATCH_FARM_SEND_INITIAL_DATA == True:
        data_series_submitted = cache.get('trend_submitted', [])
        data_series_running = cache.get('trend_running', [])
        data_series_fairshare = cache.get('trend_fairshare', [])
        data_series_ucomptime = cache.get('trend_ucomptime', [])
        hist_jcomptime = cache.get('hist_jcomptime', [])
        dist_progress = cache.get('dist_progress', [])
        data_group_submitted = cache.get('data_submitted_f', [])
        data_group_running = cache.get('data_running_f', [])
        data_group_queued = cache.get('data_queued_f', [])
    else:
        data_series_submitted = []
        data_series_running = []
        data_series_fairshare = []
        data_series_ucomptime = []
        hist_jcomptime = []
        dist_progress = []
        data_group_submitted = []
        data_group_running = []
        data_group_queued = []

    chart_submitted = format_trend_plot(farm_id, 'sj', label_submitted, series_data=data_series_submitted)
    chart_running = format_trend_plot(farm_id, 'rj', label_running, series_data=data_series_running)
    chart_fairshare = format_trend_plot(farm_id, 'fs', label_fairshare, series_data=data_series_fairshare)
    chart_ucomptime = format_trend_plot(farm_id, 'uct', label_ucomptime, series_data=data_series_ucomptime, ylabel='Time [min]')

    chart_jcomptime = format_hist_plot(farm_id, 'jct', label_jcomptime, series_data=hist_jcomptime)

    pie_chart_submitted = format_embedded_pie_chart(label_submitted, data_group_submitted, [ '17%', '50%' ])
    pie_chart_running = format_embedded_pie_chart(label_running, data_group_running, [ '50%', '50%' ])
    pie_chart_queued = format_embedded_pie_chart(label_queued, data_group_queued, [ '83%', '50%' ])

    scatter_pie_all_data = dist_progress
    embedded_pie_all = [ pie_chart_submitted, pie_chart_running, pie_chart_queued]

    chart_progress = format_dist_plot(farm_id, 'jp', label_progress, data=scatter_pie_all_data)
    chart_jsummary = format_pie_chart(farm_id, 'js', 'Jobs summary', data=embedded_pie_all)

    d['charts'] = [chart_submitted, chart_running, chart_fairshare, chart_progress, chart_jcomptime, chart_ucomptime, chart_jsummary]

    return render(request, 'batch_farm_monitor/monitor.html', d)

# tools
def prepare_data(farm):
    data_list_ts = []

    data_series_submitted = []
    data_series_running = []
    data_series_fairshare = []
    data_series_ucomptime = []

    hist_jcomptime = []
    dist_progress = []

    data_group_submitted = []
    data_group_running = []
    data_group_queued = []

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
            idx = list(g_users.keys()).index(u)
            col_idx = len(data_series_submitted)

            _lsj = [list(a) for a in zip(data_list_ts[-len(val.q_njobsS):], list(val.q_njobsS))]
            _lrj = [list(a) for a in zip(data_list_ts[-len(val.q_njobsR):], list(val.q_njobsR))]

            _n_submitted = val.q_njobsS[len(val.q_njobsS)-1]
            _n_running = val.q_njobsR[len(val.q_njobsR)-1]
            _n_queued = val.q_njobsQ[len(val.q_njobsQ)-1]

            _lfs = [list(a) for a in zip(data_list_ts[-len(val.q_fairshare):], list(val.q_fairshare))]
            _ljp = list(val.l_jobprogress)

            _ljct = histogramize(val.q_jcalctime, 24, 0, 120)
            _luct = [list(a) for a in zip(data_list_ts[-len(val.q_ucalctime):], list(val.q_ucalctime))]

            user_name = val.name
            if bmconfig.user_map is not None:
                if user_name in bmconfig.user_map:
                    user_name = bmconfig.user_map[user_name]

            data_series_submitted.append({ 'name' : user_name, 'data': _lsj, 'zIndex': col_idx, 'index': idx, '_color': col_idx })
            data_series_running.append({ 'name' : user_name, 'data': _lrj, 'zIndex': col_idx, 'index': idx, '_color': col_idx })
            data_series_fairshare.append({ 'name' : user_name, 'data': _lfs, 'zIndex': col_idx, 'index': idx, '_color': col_idx })
            data_series_ucomptime.append({ 'name' : user_name, 'data': _luct, 'zIndex': col_idx, 'index': idx, '_color': col_idx })

            dist_progress.append({ 'name' : user_name, 'data': _ljp, 'zIndex': col_idx, 'index': idx, '_color': col_idx })

            if _n_submitted > 0:
                data_group_submitted.append({ 'name' : user_name, 'y': _n_submitted, '_color': col_idx })
            if _n_running > 0:
                data_group_running.append({ 'name' : user_name, 'y': _n_running, '_color': col_idx })
            if _n_queued > 0:
                data_group_queued.append({ 'name' : user_name, 'y': _n_queued, '_color': col_idx })

            hist_jcomptime.append({ 'name' : user_name, 'data': _ljct, 'zIndex': col_idx, 'index': idx, '_color': col_idx })


        val = g_users['ALL']
        col_idx = len(data_series_submitted)

        _lsj = [list(a) for a in zip(data_list_ts, list(val.q_njobsS))]
        _lrj = [list(a) for a in zip(data_list_ts, list(val.q_njobsR))]

        data_series_submitted.append({ 'name' : val.name, 'data': _lsj, 'zIndex': -1, 'index': 99999, '_color': col_idx })
        data_series_running.append({ 'name' : val.name, 'data': _lrj, 'zIndex': -1, 'index': 99999, '_color': col_idx })

    cache.set('trend_submitted', data_series_submitted)
    cache.set('trend_running', data_series_running)
    cache.set('trend_fairshare', data_series_fairshare)
    cache.set('trend_ucomptime', data_series_ucomptime)
    cache.set('hist_jcomptime', hist_jcomptime)
    cache.set('dist_progress', dist_progress)
    cache.set('pie_submitted', data_group_submitted)
    cache.set('pie_running', data_group_running)
    cache.set('pie_queued', data_group_queued)

    for i in range(len(data_group_submitted)):
        _c = data_group_submitted[i]['_color']
        data_group_submitted[i]['color'] = '$@#Highcharts.getOptions().colors[ %d ]#@$' % _c

    for i in range(len(data_group_running)):
        _c = data_group_running[i]['_color']
        data_group_running[i]['color'] = '$@#Highcharts.getOptions().colors[ %d ]#@$' % _c

    for i in range(len(data_group_queued)):
        _c = data_group_queued[i]['_color']
        data_group_queued[i]['color'] = '$@#Highcharts.getOptions().colors[ %d ]#@$' % _c

    cache.set('data_submitted_f', data_group_submitted)
    cache.set('data_running_f', data_group_running)
    cache.set('data_queued_f', data_group_queued)

def format_trend_plot(farm, chart_data_type, title, series_data, xlabel='Time', ylabel='Jobs number'):
    chart = {
        'chart':{
            'reflow': False,
            'type': 'line',
            'zoomType': 'x',
            'events': {
                'load': "$@#function() {"
                    " time_chart_updater('" + reverse('batch_farm_monitor:monitor', args=(farm,)) + "', this, '" + chart_data_type + "');"
                    " }#@$",
                } },
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
            'title': { 'text': ylabel }, },
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
                    " hist_chart_updater('" + reverse('batch_farm_monitor:monitor', args=(farm,)) + "', this, '" + chart_data_type + "');"
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
                    " scatter_chart_updater('" + reverse('batch_farm_monitor:monitor', args=(farm,)) + "', this, '" + chart_data_type + "');"
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
            'tickInterval' : 20,
        },
        'yAxis': {
            'title': { 'text': ylabel},
            'min' : 0,
            'max': 105,
            'alignTicks' : False,
            'allowDecimals' : False,
            'tickInterval' : 10,
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
                    " pie_chart_updater('" + reverse('batch_farm_monitor:monitor', args=(farm,)) + "', this, '" + chart_data_type + "');"
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

    for i in range(bins):
        histo[i] = [ bmin + i*tick + tick/2, None ]

    for i in range(len(data)):
        val = float(data[i])
        _bin = int( (val - bmin) / tick )
        if _bin >= 0 and _bin < bins:
            histo[_bin][1] = int(histo[_bin][1] or 0) + 1

    return histo
