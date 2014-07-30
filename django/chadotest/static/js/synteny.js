//var w = d3.max([1000,document.getElementById('synteny').offsetWidth]),
var w = document.getElementById('synteny').offsetWidth,
    p = 100,
    plots_per_row = 3,
    l = (w-(p*4))/plots_per_row,
    toolbar_w = document.getElementById('zoom').offsetWidth,
    toolbar_p = (toolbar_w-l)/2,
    scroll_h = document.getElementById('toolbar').offsetHeight-toolbar_w-toolbar_p,
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

// the zoom svg
var zoom = d3.select("#zoom").append("svg")
    .attr("width", toolbar_w)
    .attr("height", toolbar_w)
    .append("g");

zoom.append("rect")
    .attr("class", "rect")
    .attr("x", toolbar_p)
    .attr("y", toolbar_p)
    .attr("width", l)
    .attr("height", l);

// the legend svg
$('#legend').css('height', scroll_h);

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
    var points = ch_data.enter().append("circle")
        .attr("class", "dot")
        .attr("r", 3.5)
        .attr("cx", function(e) { return x(e.x); })
        .attr("cy", function(e) { return y(e.y); })
        .style("fill", function(e) { return color(e.family); });

    ch_data.enter().append("text")
        .attr("class", "tip")
        .attr("x", function(e) { return x(e.x); })
        .attr("y", function(e) { return y(e.y); })
        .attr("text-anchor", "left")
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
        points.classed("selected", function(e) {
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
        
        points.classed("selected", false);
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
        points
        .transition()
            .duration(500)
            .attr("cx", function(e) { return x(e.x); })
			.attr("visibility", function(e) {
				if( e.x < domain[0] || e.x > domain[1] ) {
					return "hidden";
				} return "visible"; });
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
    // tip the genes in the selected family
    d3.selectAll(".tip").filter(function(e, j) { return e.family == d; }).style("visibility", "visible");
}).on("mouseout", function(d, i) {
    // unfade the legend
    d3.selectAll(".legend").filter(function(e) { return d != e; }).style("opacity", 1);
    // unfade the genes not in the selected family
    d3.selectAll(".dot").filter(function(e, j) { return e.family != d; }).style("opacity", 1);
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

// adds a tip to a gene
function tip(d) {
    svg.append("text")
    .attr("class", "tip")
    .attr("transform", "translate("+d.x+","+d.y+") rotate(-45)")
    .attr("text-anchor", "left")
    .html(d.name+": "+d.fmin+" - "+d.fmax);
}

