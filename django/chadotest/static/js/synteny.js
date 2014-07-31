//var w = d3.max([1000,document.getElementById('synteny').offsetWidth]),
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

// the plot matrix svg
var svg = d3.select("#synteny").append("svg")
    .attr("width", w )
    .attr("height", h )
  .append("g")
    .attr("transform", "translate(" + 0 + ",0)");

// the legend svg
var scroll = d3.select("#legend").append("svg")
    .attr("width", legend_w)
    .attr("height", legend_h)
    .append("g");

// make the plots
var i = 0;
data.plots.forEach(function(d) {

    // where is the plot located?
    var plot_x = ((i)%plots_per_row)*(p+l)+p,
        plot_y = Math.ceil((i+1)/3)*(l+p);

    // the plot's rectangle
    svg.append("rect")
        .attr("class", "rect")
        .attr("x", plot_x)
        .attr("y", (plot_y-l))
        .attr("width", l)
        .attr("height", l);

    // the x axis
    var min_x = d3.min(d.points, function(e) { return e.x; }),
        max_x = d3.max(d.points, function(e) { return e.x; });

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

    // plot the points
    var groups = ch_data.enter().append('g')
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

    // the plot's brush
    var brush = d3.svg.brush().x(x).y(y)
        .on("brush", brushmove)
        .on("brushend", brushend);

    var brush_g = svg.append("g")
        .attr("class", "brush")
        .call(brush);

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

    i++;
});

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
    d3.selectAll(".tip").filter(function(e, j) { return e.family == d; }).style("visibility", "visible");
}).on("mouseout", function(d, i) {
    // unfade the legend
    d3.selectAll(".legend").filter(function(e) { return d != e; }).style("opacity", 1);
    // unfade the genes not in the selected family
    d3.selectAll(".dot").filter(function(e, j) { return e.family != d; }).style("opacity", 1);
	d3.selectAll(".point").filter(function(e, j) { return e.family != d; }).style("opacity", 1);
	d3.selectAll(".track").style("opacity", 1);
    // remove tooltips
    d3.selectAll(".tip").filter(function(e, j) { return e.family == d; }).style("visibility", "hidden");
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

// add the query track
var num_genes = d3.max(data.query.genes, function(d) { return d.x; })+1,
    top_pad = 150;
    pad = 20,
    l_pad = 150,
    left_pad = 200,
	num_tracks = 2,
	y_h = num_tracks*30,
	query_h = y_h+pad+top_pad;

// define the scatter plot
var query = d3.select("#contextviewer")
        .append("svg")
        .attr("width", w)
        .attr("height", query_h);

// initialize the x and y scales
var x = d3.scale.linear().domain([0, num_genes-1]).range([left_pad, w-pad-l_pad]),
	y = d3.scale.linear().domain([0, num_tracks-1]).range([top_pad, y_h+top_pad]);

// the chromosome axis - there should only be one!
var yAxis = d3.svg.axis().scale(y).orient("left")
	.tickValues([0,1]) // we don't want d3 taking liberties to make things pretty
    .tickFormat(function (d, i) {
		if( i == 0 ) {
			return data.query.chromosome_name;
		} return '';
    });

query.append("g")
    .attr("class", "axis")
    .attr("transform", "translate("+(left_pad-pad)+", 0)")
    .call(yAxis);


// add the genes
var query_groups = query.selectAll(".point")
    .data(data.query.genes)
	.enter().append('g')
	.attr("transform", function(d) {
		return "translate("+x(d.x)+", "+y(d.y)+")";
	});;
	
query_groups.append("path")
    .attr("class", "point")
    .attr("d", d3.svg.symbol().type("triangle-up").size(200))
    .attr("class", "point")
    .attr("transform", function(d) { return "rotate("+((d.strand == 1) ? "90" : "-90")+")"; })
    .style("fill", function(d) { return color(d.family); });

query_groups.append("text")
    .attr("class", "tip")
	.attr("transform", "translate(0, -7) rotate(-45)")
    .attr("text-anchor", "left")
    .html(function(d) { return d.name+": "+d.fmin+" - "+d.fmax; });

// add lines from each gene to it's left neighbor
query.selectAll("path").filter(function(d, i) { return d.x != 0; }).each(draw_line);

// make thickness of lines a function of their length
var tracks = d3.selectAll(".track");
var max_width = d3.max(tracks.data());
var min_width = d3.min(tracks.data());
var width = d3.scale.linear()
    .domain([min_width, max_width])
    .range([.1, 5]);
tracks.attr("stroke-width", function(d) { return width(d); });

// draw a line between the given gene and it's left neighbor
function draw_line(d) {
    d3.selectAll("path")
    .filter(function(e, j) { return e.x == d.x-1 && e.y == d.y; })
    .each(function(e) {
        var track_group = query.append('g')
			.attr("transform", "translate("+x(e.x)+", "+y(d.y)+")");

		var track_length = x(d.x)-x(e.x);

		track_group.append("line")
        .attr("class", "track")
        //.attr("x1", x(e.x))
		.attr("x1", 0)
        .attr("x2", track_length)
        //.attr("y1", y(d.y))
        //.attr("y2", y(d.y))
		.attr("y1", 0)
		.attr("y2", 0)
        .data(function() {
			if( d.fmin > e.fmax ) {
				return [d.fmin-e.fmax];
			}
			return [e.fmin-d.fmax];
		});

		track_group.append("text")
		    //.attr("class", "tip")
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
