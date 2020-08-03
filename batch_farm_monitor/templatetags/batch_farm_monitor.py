from django import template
import json
import simplejson
from django.utils.safestring import mark_safe
from django.conf import settings
import posixpath

from ..hacks import js_call_extractor
#from ..charts import Chart, PivotChart

#try:
	#CHARTIT_JS_REL_PATH = settings.CHARTIT_JS_REL_PATH
	#if CHARTIT_JS_REL_PATH[0] == '/':
		#CHARTIT_JS_REL_PATH = CHARTIT_JS_REL_PATH[1:]
	#CHART_LOADER_URL = posixpath.join(settings.STATIC_URL, 
									#CHARTIT_JS_REL_PATH,
									#'chartloader.js')
#except AttributeError:
	#CHARTIT_JS_REL_PATH = 'chartit/js/'
	#CHART_LOADER_URL = posixpath.join(settings.STATIC_URL, 
									#CHARTIT_JS_REL_PATH,
									#'chartloader.js')

register = template.Library()

@register.filter
def show_charts(chart_list=None, render_to=''):
	"""Loads the ``Chart``/``PivotChart`` objects in the ``chart_list`` to the 
	HTML elements with id's specified in ``render_to``. 
	
	:Arguments:
	
	- **chart_list** - a list of Chart/PivotChart objects. If there is just a 
	single element, the Chart/PivotChart object can be passed directly 
	instead of a list with a single element.
	
	- **render_to** - a comma separated string of HTML element id's where the 
	charts needs to be rendered to. If the element id of a specific chart 
	is already defined during the chart creation, the ``render_to`` for that 
	specific chart can be an empty string or a space.
	
	For example, ``render_to = 'container1, , container3'`` renders three 
	charts to three locations in the HTML page. The first one will be 
	rendered in the HTML element with id ``container1``, the second 
	one to it's default location that was specified in ``chart_options`` 
	when the Chart/PivotChart object was created, and the third one in the
	element with id ``container3``.
	
	:returns:
	
	- a JSON array of the HighCharts Chart options. Also returns a link
	to the ``chartloader.js`` javascript file to be embedded in the webpage. 
	The ``chartloader.js`` has a jQuery script that renders a HighChart for 
	each of the options in the JSON array"""

	opening_embed_script = (
		'<script src="http://code.highcharts.com/highcharts.js"></script>\n'
		'<script src="http://code.highcharts.com/modules/exporting.js"></script>\n'
		'<script src="http://code.highcharts.com/modules/no-data-to-display.js"></script>\n'
		'<script type="text/javascript">\n'
		'Highcharts.setOptions({\n'
		'	global: {\n'
		'		useUTC: false },\n'
		'	lang: {\n'
		'		noData: "No data to display, wait for server to update" },\n'
		'});\n')
	closing_embed_script = (
		'</script>\n')

	tpl_embed_script = (
		'$(function () { $(\'#%s\').highcharts(\n'
		'%s\n'
		'); });\n')

	no_data_script = '<script src="http://code.highcharts.com/no-data-to-display.js"></script>\n'

	embed_script = ""

	if chart_list is not None:
		render_to_list = [s.strip() for s in render_to.split(',')]
		for hco, render_to in zip(chart_list, render_to_list):
			jsdump = js_call_extractor(json.dumps(hco))

			embed_script += tpl_embed_script % (render_to, jsdump )
	else:
		embed_script = tpl_embed_script %((), "")

	return mark_safe(opening_embed_script + embed_script + closing_embed_script)
