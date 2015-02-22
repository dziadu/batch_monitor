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

function time_chart_updater(farm, chart, chart_type) {
	// set up the updating of the chart each second

	var f = function() {
		if (chart.series.length) {
			var keys = chart.series[0].xData;
			var last = keys[keys.length-1];
			lastts = last;
		}
		else
			lastts=null

		$.getJSON('/monitor/'+farm+'/new/'+chart_type+'/?lastts='+lastts+'&callback=?', function(jsondata) {
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
					jsondata.result.splice(jsondata.result.indexOf(res[0]), 1)
				}
				else if (res.length > 1) { }
				else { chart.series[i].remove() }
			}

			var s_len = jsondata.result.length;
			for (i = 0; i < s_len; i++) {
				chart.addSeries(jsondata.result[i]);
			}
			chart.redraw();
		});
		
		chart_time_subtitle(chart)
	}

// 	f();
	chart_time_subtitle(chart)
	setInterval(function() {f()}, 60000);
}

function scatter_chart_updater(farm, chart, chart_type) {
	// set up the updating of the chart each second

	var f = function() {
		$.getJSON('/monitor/'+farm+'/new/'+chart_type+'/?callback=?', function(jsondata) {
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
								chart.series[i].data[j].color = Highcharts.getOptions().colors[ res_pie[0].data[j]._color ]
							jsondata.pie.splice(jsondata.pie.indexOf(res_pie[0]), 1)
						} else {
							console.log("++= WTF 1 +++")
							chart.series[i].data = null
						}
					} else {
						console.log("++= WTF 2 +++")
						chart.series[i].setData([])
					}
				}
			}

			var s_len = jsondata.result.length;
			for (i = 0; i < s_len; i++) {
				chart.addSeries(jsondata.result[i]);
			}
			chart.redraw();
		});

		chart_time_subtitle(chart)
	}

// 	f();
	chart_time_subtitle(chart)
	setInterval(function() {f()}, 60000);
}

function chart_time_subtitle(chart) {
	var d = new Date();
	var now = "Last update: " + d.toLocaleTimeString()
	d.setMinutes(d.getMinutes() + 1)
	var later = "Next update: " + d.toLocaleTimeString()
	var subtitle = now + " | " + later

	chart.setTitle(null, { text : subtitle })
}