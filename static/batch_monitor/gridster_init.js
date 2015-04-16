var gridster;
var mar_v = 5
var mar_h = 5
var grid_div_h = 12
var grid_div_v = 12
var grid_size_v = 400;

function reflow_chart(elem) {
	var child_nodes_len = elem.children.length;
	for (var c = 0; c < child_nodes_len; ++c)
	{
		if (elem.children[c].hasAttribute('data-highcharts-chart')) {
// 			console.log('Reflowing ' + '#'+elem.children[c].id);
			$('#'+elem.children[c].id).highcharts()._reflow();
		}
	}
}

function calc_grid_size_h() {
	var element = document.getElementById('gridster');
	var style = element.currentStyle || window.getComputedStyle(element);
	width = parseFloat(style.width);
	margin = parseFloat(style.marginLeft) + parseFloat(style.marginRight);
	padding = parseFloat(style.paddingLeft) + parseFloat(style.paddingRight);
	border = parseFloat(style.borderLeftWidth) + parseFloat(style.borderRightWidth);

// 	console.log(width, margin, padding, border, width - margin - padding - border)
	// 	var el_width = $(".gridster ul").width();
	var el_width = width - margin - padding - border;
	return el_width/grid_div_h - 2 * mar_h;	// FIXME Why 1 not 2?
}

function calc_grid_size_v() {
	var element = document.getElementById('gridster');
	var style = element.currentStyle || window.getComputedStyle(element);
	height = parseFloat(style.height);
	margin = parseFloat(style.marginTop) + parseFloat(style.marginBottom);
	padding = parseFloat(style.paddingTop) + parseFloat(style.paddingBottom);
	border = parseFloat(style.borderTopWidth) + parseFloat(style.borderBottomWidth);

// 	console.log(height, margin, padding, border, height - margin - padding - border)
	// 	var el_width = $(".gridster ul").width();
	var el_height = height - margin - padding - border;
	return el_height/grid_div_v - 2 * mar_v;	// FIXME Why 1 not 2?
}

function resize_chart(elem, w, h) {
	console.log(w);
	var child_nodes_len = elem.children.length;
	for (var c = 0; c < child_nodes_len; ++c)
	{
		if (elem.children[c].hasAttribute('data-highcharts-chart')) {
			console.log('Resizing ' + '#'+elem.children[c].id);
			$('#'+elem.children[c].id).highcharts().setSize(w, h, false);
			$('#'+elem.children[c].id).highcharts().redraw();
		}
	}
}

function recal_size() {
	console.log("*** resizing ***");
	var gridster = $(".gridster ul").gridster().data('gridster');
	gridster.options.widget_base_dimensions = [calc_grid_size_h(), calc_grid_size_v()];
//
// // 		console.log("Updating grid");
// // 		$(".gridster ul").gridster({
// // 			widget_base_dimensions: [grid_size_h, grid_size_v],
// // 		}).data('gridster');

// 	gridster.resize_widget_dimensions({ widget_base_dimensions: [grid_size_h, grid_size_v] });

	for (var i = 0; i < gridster.$widgets.length; i++)
	{
		console.log($(gridster.$widgets[i]));
		var data = $(gridster.$widgets[i]).data();
		console.log(data);
		gridster.resize_widget($(gridster.$widgets[i]), data.sizex, data.sizey);
// 			gridster.resize_widget_dimensions($(gridster.$widgets[i]), grid_size_h, grid_size_v);

// 			resize_chart($(gridster.$widgets[i])[0], grid_size_h, grid_size_v);
	}

	gridster.generate_grid_and_stylesheet();
// 		gridster.destroy();
// 		gridster.generated_stylesheets = [];
// 		gridster.init();

	console.log(gridster);

// 		for (var i = 0; i < gridster.$widgets.length; i++)
// 		{
// // 			gridster.resize_widget($(gridster.$widgets[i]), grid_size_h, grid_size_v);
// 			resize_chart($(gridster.$widgets[i])[0], grid_size_h, grid_size_v);
// 		}
}

var waitForFinalEvent = (function () {
	var timers = {};
	return function (callback, ms, uniqueId) {
		if (!uniqueId) {
			uniqueId = "Don't call this twice without a uniqueId";
		}
		if (timers[uniqueId]) {
			clearTimeout (timers[uniqueId]);
		}
		timers[uniqueId] = setTimeout(callback, ms);
	};
})();

$(window).ready(function () {
// 	localStorage.clear();

	console.log("*** Reload grid settings ***");
	var localData = JSON.parse(localStorage.getItem('positions'));
	if (localData != null)
	{
		$.each(localData, function(i, value) {
			var id_name;
			id_name = "#" + value.id;
			$(id_name).attr({"data-col":value.col, "data-row":value.row, "data-sizex":value.size_x, "data-sizey":value.size_y});
		});
	}
// })
//
// $(function() {
	console.log("*** initializing gridster ***");
	gridster = $(".gridster ul").gridster({
		widget_base_dimensions: [calc_grid_size_h(), calc_grid_size_v()],
		widget_margins: [mar_h, mar_v],
		serialize_params: function($w, wgd) {
			return {
				id: $($w).attr('id'),
				col: wgd.col,
				row: wgd.row,
				size_x: wgd.size_x,
				size_y: wgd.size_y,
			};
		},
		draggable: {
			handle: 'header',
			stop: function(event, ui) {
				var positions = JSON.stringify(this.serialize());
				localStorage.setItem('positions', positions);
			}
		},
		resize: {
			enabled: true,
			stop: function(e, ui, $widget) {
// 				console.log("+ resizing stop");
				reflow_chart($widget[0]);
				var positions = JSON.stringify(this.serialize());
				localStorage.setItem('positions', positions);
			}
		},
		min_cols: grid_div_h,
		max_cols: grid_div_h,
		min_rows: grid_div_v,
	}).data('gridster');

// 		gridster.options.widget_base_dimensions = [grid_size_h, grid_size_v];
// 		gridster.generate_grid_and_stylesheet();

// 		recal_size();
});

// 	$(window).resize(function () {
// 		waitForFinalEvent(function(){
// 		recal_size();
// 		}, 500, "some unique string");
// 	});

// 	window.addEventListener('resize', function(event){
// 		return;
// 		recal_size();
// 		gridster.options.widget_base_dimensions = [grid_size_h, grid_size_v];
// 		for (var i = 0; i < gridster.$widgets.length; i++) {
// 				gridster.resize_widget($(gridster.$widgets[i]), grid_size_h, grid_size_v);
// 				console.log($(gridster.$widgets[i]));
// 				$('#'+$(gridster.$widgets[i])[0].firstElementChild.id).highcharts().reflow();
// 		}

// 		gridster.generate_grid_and_stylesheet();

// 			document.getElementById('win_width1').innerHTML = $(document).width();
// 			document.getElementById('win_width2').innerHTML = document.documentElement.clientWidth;
// 			var gridster = $(".gridster ul").gridster().data('gridster');
// 			gridster.options.widget_base_dimensions = [(document.documentElement.clientWidth-90)/4, 500];
// 			console.log(gridster.options.widget_base_dimensions)
// 			for (var i = 0; i < gridster.$widgets.length; i++) {
// 				gridster.resize_widget($(gridster.$widgets[i]), (document.documentElement.clientWidth-100)/4, 500);
// 				console.log($(gridster.$widgets[i]));
// 				$('#'+$(gridster.$widgets[i])[0].firstElementChild.id).highcharts().reflow();
// 			}

// 			gridster.generate_grid_and_stylesheet();
// 			gridster.resize_widget_dimensions(gridster.options);
// 			{widget_base_dimensions: [100,  100]}
// 			gridster.resize_widget_dimensions( { widget_base_dimensions: [ (document.documentElement.clientWidth-100)/4, 500 ] } );

// 			for (var i = 0; i < gridster.$widgets.length; i++) {
// // 				gridster.resize_widget($(gridster.$widgets[i]), 1, 1);
// 				console.log($(gridster.$widgets[i])[0].firstElementChild.id);
// 				$('#'+$(gridster.$widgets[i])[0].firstElementChild.id).highcharts().reflow();
// 			}
// 	});

function grid_to_default() {
	localStorage.clear();
	window.location.reload();
}

