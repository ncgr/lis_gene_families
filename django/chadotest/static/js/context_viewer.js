
var viewer;

function context_viewer( container_id, color, data, gene_clicked, axis_clicked, selective_coloring ) {
	// clear the contents of the target element first
	document.getElementById(container_id).innerHTML = "";

	// get the family size map
	var family_sizes = get_family_size_map( data );
	
	// get the family id name map
	var family_names = get_family_name_map( data );

	// define dimensions of graph and a bunch of other stuff
	var w = d3.max([1000,document.getElementById(container_id).offsetWidth]),
		rect_h = 18,
		rect_pad = 2,
		top_pad = 150,
		bottom_pad = 50,
	    pad = 20,
	    l_pad = 150,
	    left_pad = 200,
		num_tracks = data.groups.length,
	    num_genes = get_track_length( data ),
		h = num_tracks*30+bottom_pad+top_pad,
        min_x = d3.min(data.groups, function(group) {
            return d3.min(group.genes, function(gene) {
                return +gene.x;
            });
        }),
        max_x = d3.max(data.groups, function(group) {
            return d3.max(group.genes, function(gene) {
                return +gene.x;
            });
        });
 
	// define the scatter plot
	viewer = d3.select("#"+container_id)
	        .append("svg")
	        .attr("width", w)
	        .attr("height", h);

	// initialize the x and y scales
	var x = d3.scale.linear().domain([min_x, max_x]).range([left_pad, w-pad-l_pad]),
		y = d3.scale.linear().domain([0, num_tracks-1]).range([top_pad, h-bottom_pad]);
	//var x = d3.scale.linear().domain([0, num_genes-1]).range([left_pad, w-pad-l_pad]),
	//	y = d3.scale.linear().domain([0, num_tracks-1]).range([top_pad, h-bottom_pad]);

	// for constructing the y-axis
	var tick_values = [];

	// add the tracks (groups)
	for( var i = 0; i < data.groups.length; i++ ) {
		// add the group to the y-axis
		tick_values.push(i);

		// make groups for the genes
		var selector = ".gene-"+i.toString();
		var gene_groups = viewer.selectAll(selector)
		    .data(data.groups[i].genes)
			.enter()
			.append("g")
			.attr("class", "gene")
			.attr("transform", function(e) {
				return "translate("+x(e.x)+", "+y(e.y)+")";
			});

		// add genes to the groups
		gene_groups.append("path")
		    .attr("d", d3.svg.symbol().type("triangle-up").size(200))
		    .attr("class", function(d) {
				if( d.x == (num_genes-1)/2 && ( selective_coloring !== undefined && selective_coloring ) ) {
					return "point focus";
				} else if ( d.family == '' ) {
					return "point no_fam";
				} else if ( family_sizes[ d.family ] == 1 &&  selective_coloring !== undefined && selective_coloring ) {
					return "point single";
				} return "point"; })
		    .attr("transform", function(d) { return "rotate("+((d.strand == 1) ? "90" : "-90")+")"; })
		    .style("fill", function(d) {
				if( d.family == '' || ( selective_coloring !== undefined && selective_coloring && family_sizes[ d.family ] == 1 ) ) {
					return "#ffffff";
				} return color(d.family);
			})
			.style("cursor", "pointer");

		gene_groups
		    .on("mouseover", function(d) {
				show_tips( d3.select(this) );
		    })
		    .on("mouseout", function(d) {
				hide_tips( d3.select(this) );
		    })
		    .on('click', function (d) {
				gene_clicked(d);
			});

		// add the tooltips
		gene_groups.append("text")
			.attr("class", "tip")
			.attr("transform", "translate(3, -14) rotate(-45)")
			.attr("text-anchor", "left")
			.html(function(e) {
				return e.name+": "+e.fmin+" - "+e.fmax;
			});

		// draw a line between the given gene and it's closest left neighbor
		function add_rails() {
			// find the neighbor
			gene_groups.each(function(d) {
				var closest;
				var neighbors = gene_groups.filter(function(e) {
					return e.y == d.y;
				});
				neighbors.each(function(e) {
					if( e.x < d.x && (closest === undefined || e.x > closest.x ) ) {
						closest = e;
					}
				});

				// draw the line
				if( closest !== undefined ) {
					var length = x(d.x)-x(closest.x);

					var rail_group = viewer.append("g")
						.attr("class", "rail")
						.attr("transform", function() {
							return "translate("+x(closest.x)+", "+y(closest.y)+")";
						})
						.attr("y", closest.y) // does nothing besides hold the datum
		    	    	.data(function() {
							if( d.fmin > closest.fmax ) {
								return [d.fmin-closest.fmax];
							}
							return [closest.fmin-d.fmax];
						});

		    	    rail_group.append("line")
						.attr("class", "line")
		    	    	.attr("x1", 0)
		    	    	.attr("x2", length)
		    	    	.attr("y1", 0)
		    	    	.attr("y2", 0);

					rail_group.append("text")
						.attr("class", "tip")
						.attr("transform", "translate("+(length/2)+", 10) rotate(45)")
						.attr("text-anchor", "left")
						.html(function(e) {
							return rail_group.data();
						});

					rail_group.moveToBack();
		    	}
			});
		}

		// add rails to the tracks
		add_rails();
	}

	// make global group selections
	var gene_groups = viewer.selectAll(".gene"),
		rail_groups = viewer.selectAll(".rail");

	// make thickness of lines a function of their "length"
	var max_width = d3.max(rail_groups.data());
	var min_width = d3.min(rail_groups.data());
	var width = d3.scale.linear()
	    .domain([min_width, max_width])
	    .range([.1, 5]);
	rail_groups.attr("stroke-width", function(e) { return width(e); });

	// construct the y-axis
	var yAxis = d3.svg.axis().scale(y).orient("left")
		.tickValues(tick_values) // we don't want d3 taking liberties to make things pretty
	    .tickFormat(function (d, i) {
	        return data.groups[d].species_name+" - "+data.groups[d].chromosome_name;
	    });

	// draw the axis of the graph
	viewer.append("g")
	    .attr("class", "axis")
	    .attr("transform", "translate("+(left_pad-pad)+", 0)")
	    .call(yAxis);

	// interact with the yaxis
	d3.selectAll(".axis text")
		.style("cursor", "pointer")
        .on("mouseover", function(d, y) {
			var gene_selection = gene_groups.filter(function(e) {
				return e.y == y;
			});
			var rail_selection = rail_groups.filter(function(e) {
				return d3.select(this).attr("y") == y;
			});
			show_tips( gene_selection, rail_selection );
        })
        .on("mouseout",  function(d, y) {
			var gene_selection = gene_groups.filter(function(e) {
				return e.y == y;
			});
			var rail_selection = rail_groups.filter(function(e) {
				return d3.select(this).attr("y") == y;
			});
			hide_tips( gene_selection, rail_selection );
        }).on("click", function(d, y){
			var gene_selection = gene_groups.filter(function(e) {
				return e.y == y;
			});
			var rail_selection = rail_groups.filter(function(e) {
				return d3.select(this).attr("y") == y;
			});
			axis_clicked( d, gene_selection, rail_selection );
		});
}
