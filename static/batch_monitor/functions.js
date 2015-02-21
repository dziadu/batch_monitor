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

	setInterval(function() {
		console.log("Hit to " + chart_type)
		//console.log("* Chart = " + chart)
		//console.log(chart)
		//console.log("* Series = " + chart.series)
		//console.log(chart.series)

		if (chart.series.length) {
			//console.log("Series length = " + chart.series.length)
			//console.log(chart.series)

			var keys = chart.series[0].xData;
			//console.log(keys)
			var last = keys[keys.length-1];
			//console.log(last)
			lastts = last;
		}
		else
			lastts=null

		$.getJSON('/monitor/1/new/'+chart_type+'/?lastts='+lastts+'&callback=?', function(jsondata) {
			if (jsondata == null)
				return

			//console.log("============================================")
			//console.log(jsondata)

			var s_len = jsondata.result.length;
			if (s_len == 0)
				return;
			//console.log(" JSON res len == " + jsondata.result.length)

			var s_len = chart.series.length;
			//console.log(" series len == " + s_len)
			for (_i = s_len; _i > 0; _i--) {
				var i = _i-1;
				var res = getObjects(jsondata.result, 'name', chart.series[i].name)

				if (res.length == 1) {
					//console.log("Updating " + chart.series[i].name);
					for (j = 0; j < res[0].data.length; j++) {
// 						console.log("Series length before = " + chart.series[i].data.length)
						chart.series[i].addPoint(res[0].data[j], false, (chart.series[i].data.length >= parseInt(jsondata.limit)) );
// 						console.log("Series length after = " + chart.series[i].data.length)
						//console.log(" Adding " + res[0].data[j])
						//console.log(" is full? " + jsondata.full)
					}
					jsondata.result.splice(jsondata.result.indexOf(res[0]), 1)
				}
				else if (res.length > 1) {
					//console.log("Ignoring " + chart.series[i].name);
				}
				else {
					//console.log("Removing " + chart.series[i].name);
					chart.series[i].remove()
					document.getElementById("search").innerHTML="Not found";
				}
			}

			var s_len = jsondata.result.length;
			for (i = 0; i < s_len; i++) {
				//console.log("Adding " + jsondata.result[i].name);
				chart.addSeries(jsondata.result[i]);
			}
			chart.redraw();
		});
	}, 60000);
}

function scatter_chart_updater(chart, chart_type) {
	// set up the updating of the chart each second

	setInterval(function() {
		//console.log("* Chart = " + chart)
		//console.log(chart)
		//console.log("* Series = " + chart.series)
		//console.log(chart.series)

// 		if (chart.series.length) {
// 			//console.log("Series length = " + chart.series.length)
// 			//console.log(chart.series)
// 
// 			var keys = chart.series[0].xData;
// 			//console.log(keys)
// 			var last = keys[keys.length-1];
// 			//console.log(last)
// 			lastts = last;
// 		}
// 		else
// 			lastts=null

		$.getJSON('/monitor/1/new/'+chart_type+'/?callback=?', function(jsondata) {
			if (jsondata == null)
				return

			//console.log("============================================")
			//console.log(jsondata)

			var s_len = jsondata.result.length;
			if (s_len == 0)
				return;
			//console.log(" JSON res len == " + jsondata.result.length)

			var s_len = chart.series.length;
			//console.log(" series len == " + s_len)
			for (_i = s_len; _i > 0; _i--) {
				var i = _i-1;
				var res = getObjects(jsondata.result, 'name', chart.series[i].name)

				if (res.length == 1) {
					console.log("Updating " + chart.series[i].name);
// 					for (j = 0; j < res[0].data.length; j++) {
// 						console.log("Series length before = " + chart.series[i].data.length)
						chart.series[i].setData(res[0].data);
// 						console.log("Series length after = " + chart.series[i].data.length)
						//console.log(" Adding " + res[0].data[j])
						//console.log(" is full? " + jsondata.full)
// 					}
					jsondata.result.splice(jsondata.result.indexOf(res[0]), 1)
				}
				else if (res.length > 1) {
					//console.log("Ignoring " + chart.series[i].name);
				}
				else {
					//console.log("Removing " + chart.series[i].name);
					chart.series[i].setData([])
					document.getElementById("search").innerHTML="Not found";
				}
			}

			var s_len = jsondata.result.length;
			for (i = 0; i < s_len; i++) {
				console.log("Adding " + jsondata.result[i].name);
				chart.addSeries(jsondata.result[i]);
			}
		});
	}, 60000);
}
