from django.core.cache import cache
from batch_monitor.models import BatchHostSettings
from decorators import json_response
from django.shortcuts import get_object_or_404, render

label_rj = 'Running jobs'
label_qj = 'Queued jobs'
label_hj = 'Hold jobs'

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
		response_data = cache.get('data_ser_tj', None)
	elif data_type == "rj":
		response_data = cache.get('data_ser_rj', None)
	elif data_type == "fs":
		response_data = cache.get('data_ser_fs', None)
	elif data_type == "jp":
		response_data = cache.get('data_jp', None)
		return {
			'result': response_data,
			'pie': [{
					'name' : label_qj,
					'data': cache.get('data_pie_qj', None),
				},
				{
					'name' : label_hj,
					'data': cache.get('data_pie_hj', None),
				}]
			}
	elif data_type == "js":
		return {
			'pie': [{
					'name' : label_rj,
					'data': cache.get('data_pie_rj', None),
				},
				{
					'name' : label_qj,
					'data': cache.get('data_pie_qj', None),
				},
				{
					'name' : label_hj,
					'data': cache.get('data_pie_hj', None),
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
