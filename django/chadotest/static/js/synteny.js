// var w = d3.max([1000,document.getElementById('synteny').offsetWidth]),
var w = document.getElementById('synteny').offsetWidth,
    p = 100,
    plots_per_row = 3,
    l = (w-(p*4))/plots_per_row,
    rect_h = 18,
    rect_p = 2,
    legend_w = document.getElementById('legend').offsetWidth-20;

var color = d3.scale.category10();

var data = JSON.parse(json);

var num_plots = data.plots.length,
    num_rows = Math.ceil(num_plots/plots_per_row),
    h = num_rows*l + (num_rows+1)*p,
    num_fams = data.families.length,
    legend_h = num_fams*(rect_h+rect_p);

// the legend svg
var scroll = d3.select("#legend").append("svg")
    .attr("width", legend_w)
    .attr("height", legend_h)
    .append("g");

// make the plots
var omit = {};
function matrix_plot() {
	$("#synteny").html('');

	// the plot matrix svg
	var svg = d3.select("#synteny").append("svg")
	    .attr("width", w )
	    .attr("height", h )
	  .append("g")
	    .attr("transform", "translate(" + 0 + ",0)");
	
	var i = 0;
	data.plots.forEach(function(d) {
	
		if( !(d.chromosome_id in omit) ) {
	
	    // where is the plot located?
	    var plot_x = ((i)%plots_per_row)*(p+l)+p,
	        plot_y = Math.ceil((i+1)/3)*(l+p);
	
		// pplot the remove button
		svg.append("image")
			.attr("class", "remove")
			.attr("x", (plot_x+l+5))
			.attr("y", (plot_y-l-27-5))
			.attr("width", 27)
			.attr("height", 27)
			.attr("xlink:href", remove_image)
			.on("click", function() {
				omit[ d.chromosome_id ] = true;
				matrix_plot();
			});
	
	    // the plot's rectangle
	    svg.append("rect")
	        .attr("class", "rect")
	        .attr("x", plot_x)
	        .attr("y", (plot_y-l))
	        .attr("width", l)
	        .attr("height", l);
	
	    // the x axis
	    var min_x = d3.min(d.points, function(e) { return e.x; }),
	        max_x = d3.max(d.points, function(e) { return e.x; }),
			x_pad = (max_x - min_x)/10;

		min_x = min_x-x_pad;
		max_x = max_x+x_pad;
	
	    var x = d3.scale.linear()
	        .domain([min_x, max_x])
	        .range([plot_x, plot_x+l]);
	
	    var xAxis = d3.svg.axis()
	        .scale(x)
	        .orient("bottom")
	        .tickValues([min_x, max_x]);
	
	    var xAxis_selection = svg.append("g")
	        .attr("class", "x axis")
	        .attr("transform", "translate(0," + plot_y + ")")
	        .call(xAxis)
	
	    xAxis_selection.append("text")
	        .attr("class", "label")
	        .attr("x", (plot_x+(l/2)))
	        .attr("y", 10)
	        .style("text-anchor", "middle")
	        .text(d.chromosome_name);
	
	    // the y axis
	    var min_y = d3.min(d.points, function(e) { return e.y; }),
	        max_y = d3.max(d.points, function(e) { return e.y; });
	
	    var y = d3.scale.linear()
	        .domain([min_y, max_y])
	        .range([plot_y, plot_y-l]);
	    
	    var yAxis = d3.svg.axis()
	        .scale(y)
	        .orient("left")
	        .tickValues([min_y, max_y]);
	    
	    svg.append("g")
	        .attr("class", "y axis")
	        .attr("transform", "translate("+plot_x+", 0)")
	        .call(yAxis)
	      .append("text")
	        .attr("class", "label")
	        .attr("transform", "translate(-10,"+(plot_y-(l/2))+") rotate(-90)")
	        .style("text-anchor", "end")
	        .text(data.query.chromosome_name);
	
	    var ch_data = svg.selectAll(d.chromosome_name)
	        .data(d.points);
	
	    // the plot's brush
	    var brush = d3.svg.brush().x(x).y(y)
	        .on("brush", brushmove)
	        .on("brushend", brushend);
	
	    var brush_g = svg.append("g")
	        .attr("class", "brush")
	        .call(brush);
	
	    // plot the points
	    var groups = ch_data.enter().append('g').attr("class", "gene")
			.attr("transform", function(e) {
				return "translate("+x(e.x)+", "+y(e.y)+")" });
			
		groups.append("circle")
	        .attr("class", "dot")
	        .attr("r", 3.5)
	        .style("fill", function(e) { return color(e.family); });
	
	    groups.append("text")
	        .attr("class", "tip")
			.attr("transform", "rotate(-45)")
	        .attr("text-anchor", "middle")
	        .html(function(e) { return e.name+": "+e.fmin+" - "+e.fmax; });
	
	    i++;
		}
	
		var extent;
	    function brushmove() {
	        extent = brush.extent();
			extent[0][1] = min_y;
			extent[1][1] = max_y;
			brush.extent(extent);
			brush_g.call(brush);
	        groups.classed("selected", function(e) {
	            is_brushed = extent[0][0] <= e.x && e.x <= extent[1][0];
	            return is_brushed;
	        });
	    }
	
		var clear_button;
	    function brushend() {
	        get_button = d3.selectAll(".clear-button").filter(function() {
				if( clear_button ) {
					return this == clear_button[0][0];
				} return false; });
	        if(get_button.empty() === true) {
	            clear_button = svg.append('text')
	                .attr("y", (plot_y+30))
	                .attr("x", (plot_x+(l/2)))
	                .attr("class", "clear-button")
	                .text("Clear Brush")
	                .style("text-anchor", "middle");
	        }
	        
	        x.domain([extent[0][0], extent[1][0]]);
	        
	        transition_data();
	        reset_axis();
			set_context();
	        
	        groups.classed("selected", false);
			brush_g.call(brush.clear());
	        
	        clear_button.on('click', function(){
	            x.domain([min_x, max_x]);
	            transition_data();
	            reset_axis();
	            clear_button.remove();
	        });
	    }
	    
	    function transition_data() {
			var domain = x.domain();
			groups.transition()
				.duration(500)
				.attr("transform", function(e) {
					return "translate("+x(e.x)+", "+y(e.y)+")";
				})
				.attr("visibility", function(e) {
					if( e.x < domain[0] || e.x > domain[1] ) {
						return "hidden";
					} return "visible";
				});
	    }
	
	    function reset_axis() {
			xAxis.tickValues(x.domain());
	        svg.transition().duration(500)
	            .selectAll(".x.axis").filter(function() { return this == xAxis_selection[0][0]; })
	            .call(xAxis);
	    }

		function set_context() {
			var domain = x.domain();
			var result_families = [];
			var added = {};
			var selected = groups.filter(function(e) {
				if( e.x >= domain[0] && e.x <= domain[1] ) {
					// no need for redundant families
					if( !(e.id in added ) ) {
						added[e.id] = 0;
						return true;
					}
				} return false;;
			});
			
			selected.each(function(e) {
				result_families.push(e.family);
			});
			var query_families = [];
			for( var i = 0; i < data.query.genes.length; i++ ) {
				var gene = data.query.genes[i];
				query_families[gene.x] = (gene.family);
			}
			var alignment = align( query_families, result_families );
			context_plot( alignment, d.chromosome_id, selected );
		}
	});
}
matrix_plot();

var legend = scroll.selectAll(".legend")
    .data(color.domain())
  .enter().append("g")
    .attr("class", "legend")
    .attr("transform", function(d, i) { return "translate(0," + i * 20 + ")"; });

legend.on("mouseover", function(d, i) {
    // fade the legend
    d3.selectAll(".legend").filter(function(e) { return d != e; }).style("opacity", .1);
    // fade the genes not in the selected family
    d3.selectAll(".dot").filter(function(e, j) { return e.family != d; }).style("opacity", .1);
	d3.selectAll(".point").filter(function(e, j) { return e.family != d; }).style("opacity", .1);
	d3.selectAll(".track").style("opacity", .1);
    // tip the genes in the selected family
	d3.selectAll(".gene").filter(function(e) { return e.family == d; }).select("text").style("visibility", "visible");
    //d3.selectAll(".tip").filter(function(e, j) { return e.family == d; }).style("visibility", "visible");
}).on("mouseout", function(d, i) {
    // unfade the legend
    d3.selectAll(".legend").filter(function(e) { return d != e; }).style("opacity", 1);
    // unfade the genes not in the selected family
    d3.selectAll(".dot").filter(function(e, j) { return e.family != d; }).style("opacity", 1);
	d3.selectAll(".point").filter(function(e, j) { return e.family != d; }).style("opacity", 1);
	d3.selectAll(".track").style("opacity", 1);
    // remove tooltips
	d3.selectAll(".gene").filter(function(e) { return e.family == d; }).select("text").style("visibility", "hidden");
});

legend.append("rect")
    .attr("x", legend_w - 18)
    .attr("width", 18)
    .attr("height", rect_h)
    .style("fill", color);

legend.append("text")
    .attr("x", legend_w - 24)
    .attr("y", 9)
    .attr("dy", ".35em")
    .style("text-anchor", "end")
    .text(function(d) {
        var fams = []
        for( i = 0; i < data.families.length; i++) {
            if( data.families[i].id == d ) { 
                fams.push( data.families[i].name );
            }
        }
        return fams.join();
    });

// a helper function that moves things to the back
d3.selection.prototype.moveToBack = function() { 
    return this.each(function() { 
        var firstChild = this.parentNode.firstChild; 
        if (firstChild) { 
            this.parentNode.insertBefore(this, firstChild); 
        } 
    }); 
};

// a helper function that moves things to the front
d3.selection.prototype.moveToFront = function() {
	return this.each(function() {
		this.parentNode.appendChild(this);
	});
};

var num_genes = d3.max(data.query.genes, function(d) { return d.x; })+1,
    top_pad = 150;
    pad = 20,
    l_pad = 150,
    left_pad = 200,
	num_tracks = 2,
	y_h = num_tracks*30,
	query_h = y_h+pad+top_pad;

// add the query track
function context_plot( alignment, chromosome_id, selected ) {
	$("#contextviewer").html('');

	// get the plot belonging to the chromsome_id
	var plot;
	if( !(chromosome_id === undefined) ) {
		for( var i = 0; i < data.plots.length; i++ ) {
			if( data.plots[i].chromosome_id === chromosome_id ) {
				plot = data.plots[i];
				break;
			}
		}
	}

	// define the scatter plot
	var query = d3.select("#contextviewer")
	        .append("svg")
	        .attr("width", w)
	        .attr("height", query_h);
	
	// initialize the x and y scales
	var x = d3.scale.linear().range([left_pad, w-pad-l_pad]),
		y = d3.scale.linear().domain([0, num_tracks-1]).range([top_pad, y_h+top_pad]);

	// finds the x domain and coordinates for the result genes
	var start_offset = 0;
	var x_map = {};
	var pionts;
	if( !(plot === undefined || alignment === undefined || selected === undefined) ) {
		points = [];
		selected.each(function(d) {
			points.push(d);
		});
		var seq_length = 0,
			stop_offset = 0;
		var seq = alignment[0],
			ref = alignment[1];
		var j, step, x_pos = 0;
		if( alignment[2] ) {
			j = points.length-1;
			step = -1;
		} else {
			j = 0;
			step = 1;
		}
		var in_between = [];
		// insertions not on the ends of the query sequence don't contribute to the length
		for( var i = 0; i < seq.length; i++ ) {
			if( seq_length == 0 && seq[i] == -1 ) {
				start_offset++;
				x_map[points[j].id] = x_pos;
				j = j+step;
				x_pos++;
			} else if( stop_offset > 0 && seq[i] != -1 ) {
				seq_length++;
				for( var k = 0; k < in_between.length; k++ ) {
					x_map[in_between[k]] = (x_pos-1)+(k+1)*(1.0/(stop_offset+1));
				}
				stop_offset = 0;
				in_between = [];
				if( ref[i] != -1 ) {
					x_map[points[j].id] = x_pos;
					j = j+step;
				}
				x_pos++;
			} else if( seq_length > 0 && seq[i] == -1 ) {
				in_between.push(points[j].id);
				j = j+step;
				stop_offset++;
			} else {
				seq_length++;
				if( ref[i] != -1 ) {
					x_map[points[j].id] = x_pos;
					j = j+step;
				}
				x_pos++;
			}
		}
		j = j-(step*stop_offset);
		for( var k = 0; k < stop_offset; k++ ) {
			x_map[points[j].id] = x_pos;
			x_pos++;
			j = j+step;
		}
		x.domain([0, start_offset+seq_length+stop_offset-1]);
	} else {
		x.domain([0, num_genes-1]);
	}
	
	// the chromosome axis - there should only be one!
	var yAxis = d3.svg.axis().scale(y).orient("left")
		.tickValues([0,1]) // we don't want d3 taking liberties to make things pretty
	    .tickFormat(function (d, i) {
			if( i == 0 ) {
				return data.query.chromosome_name;
			} else if( !(plot === undefined) ) {
				return plot.chromosome_name;
			} return '';
	    });
	
	var query_axis = query.append("g")
	    .attr("class", "axis")
	    .attr("transform", "translate("+(left_pad-pad)+", 0)")
	    .call(yAxis);
	
	// interact with the axis
	query_axis.selectAll("text")
		.on("mouseover", function(d, i) {
			if( i == 0 ) {
				query.selectAll(".gene").filter(function(e) {
					return e.y != 0;
				}).style("opacity", .1);
				query.selectAll('.query_tip').style("visibility", "visible");
			} else {
				query.selectAll(".gene").filter(function(e) {
					return e.y == 0;
				}).style("opacity", .1);
				query.selectAll('.result_tip').style("visibility", "visible");
			}
		})
		.on("mouseout",  function(d, i) {
			if( i == 0 ) {
				query.selectAll(".gene").filter(function(e) {
					return e.y != 0;
				}).style("opacity", 1);
				query.selectAll('.query_tip').style("visibility", "hidden");
			} else {
				query.selectAll(".gene").filter(function(e) {
					return e.y == 0;
				}).style("opacity", 1);
				query.selectAll('.result_tip').style("visibility", "hidden");
			}
		});
	
	
	// add the query genes
	var query_groups = query.selectAll(".query_point")
	    .data(data.query.genes)
		.enter().append('g').attr("class", "gene")
		.attr("transform", function(d) {
			return "translate("+x(start_offset+d.x)+", "+y(d.y)+")";
		});
		
	query_groups.append("path")
	    .attr("class", "point")
	    .attr("d", d3.svg.symbol().type("triangle-up").size(200))
	    .attr("transform", function(d) { return "rotate("+((d.strand == 1) ? "90" : "-90")+")"; })
	    .style("fill", function(d) { return color(d.family); });
	
	query_groups.append("text")
	    .attr("class", "query_tip")
		.attr("transform", "translate(0, -7) rotate(-45)")
	    .attr("text-anchor", "left")
	    .html(function(d) { return d.name+": "+d.fmin+" - "+d.fmax; });

	query_groups.each(draw_line);

	// add the result genes
	if( !(plot === undefined || alignment === undefined || selected === undefined) ) {
		var flip = ( alignment[2] ? -1 : 1 );
		var result_groups = query.selectAll(".result_point")
		    .data(selected.data())
			.enter().append('g').attr("class", "gene")
			.attr("transform", function(d) {
				return "translate("+x(x_map[d.id])+", "+y(1)+")";
			});
			
		result_groups.append("path")
		    .attr("class", "point")
		    .attr("d", d3.svg.symbol().type("triangle-up").size(200))
		    .attr("transform", function(d) { return "rotate("+((flip*d.strand == 1) ? "90" : "-90")+")"; })
		    .style("fill", function(d) { return color(d.family); });
		
		result_groups.append("text")
		    .attr("class", "result_tip")
			.attr("transform", "translate(0, -7) rotate(-45)")
		    .attr("text-anchor", "left")
		    .html(function(d) { return d.name+": "+d.fmin+" - "+d.fmax; });

		result_groups.each(function(d) {
			draw_temp_line( d, alignment[2] );
		});
	}

	// add lines from each gene to it's left neighbor
	//query.selectAll("path").filter(function(d, i) { return d.x != 0; }).each(draw_line);
	//query.selectAll(".gene").each(function(d) { console.log(d); });
	
	// make thickness of lines a function of their length
	var tracks = d3.selectAll(".track");
	var max_width = d3.max(tracks.data());
	var min_width = d3.min(tracks.data());
	var width = d3.scale.linear()
	    .domain([min_width, max_width])
	    .range([.1, 5]);
	tracks.attr("stroke-width", function(d) { 
		console.log(this);
		var diff = x.invert(d3.select(this).attr("x2"))-x.invert(d3.select(this).attr("x1"));
		return width(d)/diff; });
	
	// draw a line between the given gene and it's left neighbor
	function draw_line(d) {
	    d3.selectAll("path")
	    .filter(function(e, j) { 
			return e.x == d.x-1 && e.y == d.y; })
	    .each(function(e) {
	        var track_group = query.append('g')
				.attr("transform", "translate("+x(start_offset+e.x)+", "+y(d.y)+")");
	
			var track_length = x(d.x)-x(e.x);
	
			track_group.append("line")
	        .attr("class", "track")
			.attr("x1", 0)
	        .attr("x2", track_length)
			.attr("y1", 0)
			.attr("y2", 0)
	        .data(function() {
				if( d.fmin > e.fmax ) {
					return [d.fmin-e.fmax];
				}
				return [e.fmin-d.fmax];
			});
	
			track_group.append("text")
			    .attr("class", "query_tip")
				.attr("transform", "translate("+(track_length/2)+", 7) rotate(45)")
			    .attr("text-anchor", "left")
			    .html(function() {
					if( e.fmax < d.fmin ) {
						return d.fmin-e.fmax;
					} return e.fmin-d.fmax;
				});
	
	        track_group.moveToBack();
	    });
	}

	function draw_temp_line(d, flipped) {
		var d_x, neighbor, closest = -1;
		d_x = x_map[d.id];
		for( k in x_map ) {
			if( x_map[ k ] > closest && x_map[ k ] < d_x ) {
				closest = x_map[ k ];
				neighbor = k;
			}
		}
	    d3.selectAll("path")
	    .filter(function(e, j) { 
			if( !( neighbor === undefined ) ) {
				return e.id == neighbor;
			} return false;
		})
	    .each(function(e) {
	        var track_group = query.append('g')
				.attr("transform", "translate("+x(closest)+", "+y(1)+")");
	
			var track_length = x(d_x)-x(closest);
	
			track_group.append("line")
	        .attr("class", "track")
			.attr("x1", 0)
	        .attr("x2", track_length)
			.attr("y1", 1)
			.attr("y2", 1)
	        .data(function() {
				if( d.fmin > e.fmax ) {
					return [d.fmin-e.fmax];
				}
				return [e.fmin-d.fmax];
			});
	
			track_group.append("text")
			    .attr("class", "query_tip")
				.attr("transform", "translate("+(track_length/2)+", 7) rotate(45)")
			    .attr("text-anchor", "left")
			    .html(function() {
					if( e.fmax < d.fmin ) {
						return d.fmin-e.fmax;
					} return e.fmin-d.fmax;
				});
	
	        track_group.moveToBack();
	    });
	}
	
	// mouseover genes
	d3.selectAll(".gene").on("mouseover", function(d, i) {
		var point  = d3.select(this).select(".point");
		if( !point.empty() ) {
			d3.selectAll(".point").filter(function(e, j) { return e != d; }).style("opacity", .1);
			d3.selectAll(".track").style("opacity", .1);
		} else {
			d3.selectAll(".dot").filter(function(e, j) { return e != d; }).style("opacity", .1);
		}
	    // tip the genes in the selected family
		d3.select(this).select("text").style("visibility", "visible");
	}).on("mouseout", function(d, i) {
	    // unfade the genes 
		d3.selectAll(".point").style("opacity", 1);
		d3.selectAll(".track").style("opacity", 1);
		d3.selectAll(".dot").style("opacity", 1);
	    // remove tooltips
		d3.select(this).select("text").style("visibility", "hidden");
	});
}
context_plot();
