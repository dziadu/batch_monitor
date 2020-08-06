from django.core.cache import cache
from batch_farm_monitor.models import BatchHostSettings
from batch_farm_monitor.decorators import json_response
from django.shortcuts import get_object_or_404, render
from django.http import JsonResponse
#import json
import simplejson as json

label_submitted = 'Submitted jobs'
label_running = 'Running jobs'
label_queued = 'Queued jobs'

@json_response
def jsonreq(request, farm_id, data_type):
    farm = get_object_or_404(BatchHostSettings, id=farm_id)

    g_ts = cache.get("time_stamp", None)

    if 'lastts' in request.GET:
        try:
            last_ts = int(request.GET['lastts'])
        except ValueError:
            last_ts = 0
    else:
        last_ts = 0

    if g_ts is None:
        return None

    if data_type == "sj":
        response_data = cache.get('trend_submitted', None)
    elif data_type == "rj":
        response_data = cache.get('trend_running', None)
    elif data_type == "fs":
        response_data = cache.get('trend_fairshare', None)
    elif data_type == "uct":
        response_data = cache.get('trend_ucomptime', None)
    elif data_type == "jp":
        response_data = cache.get('dist_progress', None)
        return {
            'result': response_data,
            }
    elif data_type == "js":
        print(cache.get('pie_submitted', None))
        return {
            'pie': [
                {
                    'name' : label_submitted,
                    'data': cache.get('pie_submitted', None),
                },
                {
                    'name' : label_running,
                    'data': cache.get('pie_running', None),
                },
                {
                    'name' : label_queued,
                    'data': cache.get('pie_queued', None),
                }
            ]}
    elif data_type == "jct":
        response_data = cache.get('hist_jcomptime', None)
        return {
            'result': response_data,
        }
    else:
        response_data = None

    if response_data is None:
        return None

    lt = int(last_ts)
    if lt == 0:
        return { 'limit': g_ts.colsize, 'result': response_data }

    _data = response_data[0]['data']
    _len = len(_data)

    #print("*************")
    #print(_data)
    #print(_len)
    #print(lt)
    #for i in reversed(range(_len)):
        #print(i)
        #print(int(_data[i][0]))
        #if int(_data[i][0]) <= lt:
            #_response_data = response_data
            #for j in range(len(response_data)):
                #_response_data[j]['data'] = response_data[j]['data'][i+1:_len]
            #return { 'limit': g_ts.colsize, 'result': _response_data }

    _response_data = response_data

    """ iterate over each series/user """
    for j in range(len(response_data)):

        _data = response_data[j]['data']
        _len = len(_data)

        for i in reversed(range(_len)):
            if int(_data[i][0]) <= lt:
                _response_data[j]['data'] = response_data[j]['data'][i+1:_len]
                break

            #return { 'limit': g_ts.colsize, 'result': _response_data }

    return { 'limit': g_ts.colsize, 'result': _response_data }
