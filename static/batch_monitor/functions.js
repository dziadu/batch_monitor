// find all keys with given value in object

var update_period_ms = 60000;

function getObjects(obj, key, val) {
	var objects = [];
	for (var i in obj) {
		if (!obj.hasOwnProperty(i)) continue;
		if (typeof obj[i] == 'object') {
			objects = objects.concat(getObjects(obj[i], key, val));
		} else if (i == key && obj[key] == val) {
			objects.push(obj);
		}
	}
	return objects;
}

// configure periodical update of the time chart
function time_chart_updater(farm, chart, chart_data_type) {
	var f = function() {
		if (chart.series.length) {
			var keys = chart.series[0].xData;
			var last = keys[keys.length-1];
			lastts = last;
		}
		else
			lastts=null

		$.getJSON('/monitor/'+farm+'/json/'+chart_data_type+'/?lastts='+lastts+'&callback=?', function(jsondata) {
			if (jsondata == null)
				return

			var s_len = jsondata.result.length;
			if (s_len == 0)
				return;

			var s_len = chart.series.length;
			for (_i = s_len; _i > 0; _i--) {
				var i = _i-1;
				var res = getObjects(jsondata.result, 'name', chart.series[i].name)
				if (res.length == 1) {
					for (j = 0; j < res[0].data.length; j++) {
						chart.series[i].addPoint(res[0].data[j], false, (chart.series[i].data.length >= parseInt(jsondata.limit)) );
					}
					// fix color of the series
					chart.series[i].update({
						color: Highcharts.getOptions().colors[ res[0]._color ],
						zIndex: res[0].zIndex,
						index: res[0].index,
					})
					jsondata.result.splice(jsondata.result.indexOf(res[0]), 1)
				}
				else if (res.length > 1) { }
				else { chart.series[i].remove() }
			}

			var s_len = jsondata.result.length;
			for (i = 0; i < s_len; i++) {
				var ser = chart.addSeries(jsondata.result[i]);
				// fix color of the series
				ser.update({
					color: Highcharts.getOptions().colors[ jsondata.result[i]._color ],
					zIndex: jsondata.result[i].zIndex,
					index: jsondata.result[i].index,
				})
			}
			chart.redraw();
		});
		
		chart_time_subtitle(chart)
	}

	f();
	chart_time_subtitle(chart)

	// set up the updating of the chart each second
	setInterval(function() {f()}, update_period_ms);
}

// configure periodical update of the hist chart
function hist_chart_updater(farm, chart, chart_data_type) {
	var f = function() {
		$.getJSON('/monitor/'+farm+'/json/'+chart_data_type+'/?callback=?', function(jsondata) {
			if (jsondata == null)
				return

			var s_len = jsondata.result.length;
			if (s_len == 0)
				return;

			var s_len = chart.series.length;
			for (_i = s_len; _i > 0; _i--) {
				var i = _i-1;
				var res = getObjects(jsondata.result, 'name', chart.series[i].name)

				if (res.length == 1) {
					chart.series[i].setData(res[0].data);
					chart.series[i].update({
						color: Highcharts.getOptions().colors[ res[0]._color ],
						zIndex: res[0].zIndex,
						index: res[0].index,
					})
					jsondata.result.splice(jsondata.result.indexOf(res[0]), 1)
				}
				else if (res.length > 1) { }
				else { chart.series[i].remove() }
			}

			var s_len = jsondata.result.length;
			for (i = 0; i < s_len; i++) {
				var ser = chart.addSeries(jsondata.result[i]);
				ser.update({
					color: Highcharts.getOptions().colors[ jsondata.result[i]._color ],
					zIndex: jsondata.result[i].zIndex,
					index: jsondata.result[i].index,
				})
			}

			chart.redraw();
		});

		chart_time_subtitle(chart)
	}

	f();
	chart_time_subtitle(chart)

	// set up the updating of the chart each second
	setInterval(function() {f()}, update_period_ms);
}

// configure periodical update of the scatter+pie charts
function scatter_chart_updater(farm, chart, chart_data_type) {
	var f = function() {
		$.getJSON('/monitor/'+farm+'/json/'+chart_data_type+'/?callback=?', function(jsondata) {
			if (jsondata == null)
				return

			var s_len = jsondata.result.length;
			if (s_len == 0)
				return;

			var s_len = chart.series.length;
			for (_i = s_len; _i > 0; _i--) {
				var i = _i-1;
				var res = getObjects(jsondata.result, 'name', chart.series[i].name)

				if (res.length == 1) {
					chart.series[i].setData(res[0].data);
					chart.series[i].update({
						color: Highcharts.getOptions().colors[ res[0]._color ],
						zIndex: res[0].zIndex,
						index: res[0].index,
					})
					jsondata.result.splice(jsondata.result.indexOf(res[0]), 1)
				}
				else if (res.length > 1) { }
				else {
					if (chart.series[i].type == 'pie') {
						var res_pie = getObjects(jsondata.pie, 'name', chart.series[i].name)
						if (res_pie.length == 1) {
							chart.series[i].setData(res_pie[0].data)
							var d_len = res_pie[0].data.length
							for (j = 0; j < d_len; j++)
								chart.series[i].data[j].update({
									color: Highcharts.getOptions().colors[ res_pie[0].data[j]._color ]
								})
							jsondata.pie.splice(jsondata.pie.indexOf(res_pie[0]), 1)
						} else {
							chart.series[i].data = null
						}
					} else {
						chart.series[i].remove()
					}
				}
			}

			var s_len = jsondata.result.length;
			for (i = 0; i < s_len; i++) {
				var ser = chart.addSeries(jsondata.result[i]);
				ser.update({
					color: Highcharts.getOptions().colors[ jsondata.result[i]._color ],
					zIndex: jsondata.result[i].zIndex,
					index: jsondata.result[i].index,
				})
			}

			chart.redraw();
		});

		chart_time_subtitle(chart)
	}

// 	f();
	chart_time_subtitle(chart)

	// set up the updating of the chart each second
	setInterval(function() {f()}, update_period_ms);
}

// configure periodical update of the scatter+pie charts
function pie_chart_updater(farm, chart, chart_data_type) {
	var f = function() {
		$.getJSON('/monitor/'+farm+'/json/'+chart_data_type+'/?callback=?', function(jsondata) {
			if (jsondata == null)
				return

			var s_len = chart.series.length;
			for (_i = s_len; _i > 0; _i--) {
				var i = _i-1;
				var res_pie = getObjects(jsondata.pie, 'name', chart.series[i].name)
				if (res_pie.length == 1) {
					chart.series[i].setData(res_pie[0].data)
					var d_len = res_pie[0].data.length
					for (j = 0; j < d_len; j++)
						chart.series[i].data[j].update({
							color: Highcharts.getOptions().colors[ res_pie[0].data[j]._color ]
						})
					jsondata.pie.splice(jsondata.pie.indexOf(res_pie[0]), 1)
				} else {
					chart.series[i].data = null
				}
			}

			chart.redraw();
		});

		chart_time_subtitle(chart)
	}

	f();
	chart_time_subtitle(chart)

	render_label(chart, 'Total jobs', 0.17, 0.10)
	render_label(chart, 'Running jobs', 0.50, 0.10)
	render_label(chart, 'Queued jobs', 0.83, 0.10)

	chart.series[0].update({
		center: [ chart.plotLeft + (0.17 * (chart.plotWidth-60)), '50%' ],
	});
	chart.series[1].update({
		center: [ chart.plotLeft + (0.50 * (chart.plotWidth-60)), '50%' ],
	});
	chart.series[2].update({
		center: [ chart.plotLeft + (0.83 * (chart.plotWidth-60)), '50%' ],
	});

	// set up the updating of the chart each second
	setInterval(function() {f()}, update_period_ms);
}

function render_label(chart, text, center_x, center_y) {
	elem = chart.renderer.label(text, chart.plotLeft, 0, 'callout', 0, 0)
		.css({
			color: '#FFFFFF',
		}).attr({
			fill: 'rgba(0, 0, 0, 0.75)',
			padding: 8,
			r: 5,
			zIndex: 6,
		})
		.add();

	box = elem.getBBox();

	elem.attr({
		x: chart.plotLeft + (center_x * (chart.plotWidth-60)) - (0.5 * box.width) + 30,
		y: chart.plotTop + (center_y * chart.plotHeight) - (0.5 * box.height),
	})
}

function chart_time_subtitle(chart) {
	var d = new Date();
	var now = "Last update: " + d.toLocaleTimeString()
	d.setMilliseconds(d.getMilliseconds() + update_period_ms)
	var later = "Next update: " + d.toLocaleTimeString()
	var subtitle = now + " | " + later

	chart.setTitle(null, { text : subtitle })
}