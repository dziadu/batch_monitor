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

function time_chart_updater(chart, chart_type) {
	// set up the updating of the chart each second

	var f = function() {
		if (chart.series.length) {
			var keys = chart.series[0].xData;
			var last = keys[keys.length-1];
			lastts = last;
		}
		else
			lastts=null

		$.getJSON('/monitor/1/new/'+chart_type+'/?lastts='+lastts+'&callback=?', function(jsondata) {
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
	}

// 	f();
	setInterval(function() {f()}, 60000);
}

function scatter_chart_updater(chart, chart_type) {
	// set up the updating of the chart each second

	var f = function() {
		$.getJSON('/monitor/1/new/'+chart_type+'/?callback=?', function(jsondata) {
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
				else { chart.series[i].setData([]) }
			}

			var s_len = jsondata.result.length;
			for (i = 0; i < s_len; i++) {
				chart.addSeries(jsondata.result[i]);
			}
		});
	}

// 	f();
	setInterval(function() {f()}, 60000);
}
