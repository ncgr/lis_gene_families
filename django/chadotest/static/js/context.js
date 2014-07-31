// a helper function that moves things to the back
d3.selection.prototype.moveToBack = function() { 
    return this.each(function() { 
        var firstChild = this.parentNode.firstChild; 
        if (firstChild) { 
            this.parentNode.insertBefore(this, firstChild); 
        } 
    }); 
};

// define dimensions of graph and data source
var w = d3.max([1000,document.getElementById('contextviewer').offsetWidth]),
    h = 460,
	rect_h = 18,
	rect_pad = 2;
    top_pad = 150;
    pad = 20,
    l_pad = 150,
    left_pad = 200,
    data_url = '/static/js/context.json',
    color = d3.scale.category20();
 
// define the scatter plot
var svg = d3.select("#contextviewer")
        .append("svg")
        .attr("width", w)
        .attr("height", h);
 
// define x and y scales for translating data onto the graph
var x, y;
 
// define the axis of the graph
var xAxis, yAxis;
 
// draw some placeholder loading text
svg.append("text")
    .attr("class", "loading")
    .text("Loading ...")
    .attr("x", function () { return (w-l_pad)/2; })
    .attr("y", function () { return h/2-5; });

// the data loading function
//d3.json(data_url, function (context_data) {
var context_data = JSON.parse(context_json);
    // count the number of tracks and genes per track
    var num_tracks = context_data.tracks.length,
        num_genes = d3.max(context_data.genes, function(d) { return +d.x; })+1,
		num_fams = context_data.families.length,
		y_h = num_tracks*30,
		new_h = d3.max([y_h, num_fams*(rect_h+rect_pad)])+pad+top_pad;

    // initialize the x and y scales
    x = d3.scale.linear().domain([0, num_genes-1]).range([left_pad, w-pad-l_pad]),
    y = d3.scale.linear().domain([0, num_tracks-1]).range([top_pad, y_h+top_pad]);

    // initialize the axes
    //xAxis = d3.svg.axis().scale(x).orient("bottom")
    //    .ticks(num_genes)
    //    .tickFormat(function (d, i) {
    //        return '';
    //    });
	// y-axis helper list
	var list = [];
	for (var i = 0; i < num_tracks; i++) {
		    list.push(i);
	}
    yAxis = d3.svg.axis().scale(y).orient("left")
		.tickValues(list) // we don't want d3 taking liberties to make things pretty
        //.ticks(num_tracks, 1)
        .tickFormat(function (d, i) {
            return context_data.tracks[d].species_name+" - "+context_data.tracks[d].chromosome_name;
        });
 
    // remove the placeholder text
    svg.selectAll(".loading").remove();

    // resize the graph
    svg.style("height", new_h+"px");
 
    // draw the axis of the graph
    //svg.append("g")
    //    .attr("class", "axis")
    //    .attr("transform", "translate(0, "+(h-pad)+")")
    //    .call(xAxis);
     
    svg.append("g")
        .attr("class", "axis")
        .attr("transform", "translate("+(left_pad-pad)+", 0)")
        .call(yAxis);

    // interact with the yaxis
    d3.selectAll(".axis text")
            .on("mouseover", function(d, i) {
				// fade the legend
            	d3.selectAll(".legend").style("opacity", .1);
                // fade the unselected tracks
                d3.selectAll(".track").filter(function(e) { return d3.select(this).attr('y1') != y(d); }).style("opacity", .1);
                // fade genes not on the selected chromosome
                d3.selectAll("path").filter(function(e) { return !(typeof e === "number") && d != e.y; })
                .style("opacity", .1);
                // add a tooltip for each gene on the selected track
                d3.selectAll("path")
                .filter(function(e, j) { return d == e.y; })
                .each(tip_gene);
                // add a tooltip for each line on the selected track
                d3.selectAll(".track").filter(function(e) { return d3.select(this).attr('y1') == y(d); }).each(tip_rail_on_track);
            })
            .on("mouseout",  function(d) {
				// unfade the legend
            	d3.selectAll(".legend").style("opacity", 1);
                // unfade the unselected tracks
                d3.selectAll(".track").filter(function(e, j) { return d != e.y1; }).style("opacity", 1);
                // unfade the genes not on the selected chromosome
                d3.selectAll("path").filter(function(e) { return !(typeof e === "number") && d != e.y; })
                .style("opacity", 1);
                // remove tooltips
                d3.selectAll(".tip").remove();
            }).on("click", function(d){
				// add the track's links to the content box
				var l1 = '<a href="'+organism_link+context_data.tracks[d].species_id+'/">'+context_data.tracks[d].species_name+'</a>',
					l2 = '<a href="'+feature_link+context_data.tracks[d].chromosome_id+'/">'+context_data.tracks[d].chromosome_name+'</a>',
					l3 = '<a href="'+search_link,
					l4 = '<a href="'+synteny_link,
					l5 = '<a href="'+synteny_link2;
				var genes = '<ul>';
				var families = [];
				d3.selectAll("path")
				.filter(function(e) { return !(typeof e === "number") && d == e.y; })
				.sort(function(a, b) { return a.x - b.x; })
				.each(function(f) {
					genes += '<li><a href="'+feature_link+f.id+'/">'+f.name+'</a>: '+f.fmin+' - '+f.fmax+'</li>';
					if( f.x == (num_genes-1)/2 ) {
						l3 += f.id+'/';
						l4 += f.id+'/';
						l5 += f.id+'/';
					}
				});
				genes += '</ul>';
				l3 += '">Find similar tracks</a>';
				l4 += '">Synteny miner</a>';
				l5 += '">Synteny miner spaced</a>';
				//l3 += families.join(',')+'">Find similar tracks</a>';
				$("#contextcontent").html(l5+'<br />'+l4+'<br />'+l3+'<br />'+l1+' - '+l2+genes);
			});

    // add the genes
    svg.selectAll(".point")
        .data(context_data.genes)
    .enter().append("path")
        .attr("class", "point")
        .attr("d", d3.svg.symbol().type("triangle-up").size(200))
        .on("mouseover", function(d, i) {
			// fade the legend
			d3.selectAll(".legend").style("opacity", .1);
            // fade the tracks
            d3.selectAll(".track").style("opacity", .1);
            // fade all other genes
            d3.selectAll("path")
            .filter(function(e, j) { return d != e; })
            .style("opacity", .1);
            // add a tooltip
            tip_gene(d);
        })
        .on("mouseout", function(d) {
			// unfade the legend
			d3.selectAll(".legend").style("opacity", 1);
            // unfade the tracks
            d3.selectAll(".track").style("opacity", 1);
            // unfade all other genes
            d3.selectAll("path")
            .filter(function(e, j) { return d != e; })
            .style("opacity", 1);
            // remove a tooltip
            d3.select(".tip").remove();
        })
        .on('click', function (d) {
			$.ajax({
                url:phylo_ajax_link,
                data: {
                // this is actually a phylonode_id
                gene: d.id,
                // all pages are protected against csrf so we need to pass the token for this page
                    csrfmiddlewaretoken: '{{ csrf_token }}'
                },
                contentType: "application/json;charset=utf-8",
                dataType: "json",
                success: function(data) {
                // pull the data out of the json we get back
                var html = '<h4>'+data.label+'</h4>'
                for (var i = 0; i < data.links.length; i++) {
                    for (var key in data.links[i]) {
                        html += '<a href="'+data.links[i][key]+'">'+key+'</a><br/>'
                    }
                }
                if (data.meta) {
                    html += '<p>'+data.meta+'</p>'
                }
                $('#contextcontent').html(html);
                },
                error: function(ts) { 
                // this is for debugging, not production!
                    alert(ts.responseText);
                }
            });

		})
        .attr("class", function(d) { return (d.x == (num_genes-1)/2) ? "point focus" : "point"; })
        .attr("transform", function(d) { return "translate(" + x(d.x) + "," + y(d.y) + ") rotate("+((d.strand == 1) ? "90" : "-90")+")"; })
        .style("fill", function(d) { return color(d.family); })
        .append("text").text("blah");

    // add lines from each gene to it's left neighbor
    svg.selectAll("path").filter(function(d, i) { return d.x != 0; }).each(draw_line);

    // make thickness of lines a function of their length
    var tracks = d3.selectAll(".track");
    var max_width = d3.max(tracks.data());
    var min_width = d3.min(tracks.data());
    var width = d3.scale.linear()
        .domain([min_width, max_width])
        .range([.1, 5]);
    tracks.attr("stroke-width", function(d) { return width(d); });

    // make the legend
    var legend = svg.selectAll(".legend")
        .data(color.domain())
        .enter().append("g")
        .attr("class", "legend")
        .attr("transform", function(d, i) { return "translate(0," + i * 20 + ")"; })
        .on("mouseover", function(d, i) {
			// fade the legend
            d3.selectAll(".legend").style("opacity", .1);
            // fade the tracks
            d3.selectAll(".track").style("opacity", .1);
            // fade genes not in selected family
            d3.selectAll("path")
            // I'm too lazy to actually compare the arrays... and I don't know where these random numbers are coming from
            .filter(function(e, j) { return !(typeof e === "number") && d.join() != e.family.join(); })
            .style("opacity", .1);
            // add a tooltip for each gene in the selected family
            d3.selectAll("path")
            .filter(function(e, j) { return !(typeof e === "number") && d.join() == e.family.join(); })
            .each(tip_gene);
        })
        .on("mouseout",  function(d) {
			// unfade the legend
            d3.selectAll(".legend").style("opacity", 1);
            // unfade track
            d3.selectAll(".track").style("opacity", 1);
            // unfade the genes not in the selected family
            d3.selectAll("path")
            .filter(function(e, j) { return !(typeof e === "number") && d.join() != e.family.join(); })
            .style("opacity", 1);
            // remove tooltips
            d3.selectAll(".tip").remove();
		})
        .on('click', function (d) {
			// add the families' links to the content box
			var fams = [];
			for( i = 0; i < context_data.families.length; i++ ) {
				for( j = 0; j < d.length; j++ ) {
					if( context_data.families[i].id == d[j]) {
						fams.push('<a href="'+phylo_link+d[j]+'/">'+context_data.families[i].name+'</a>');
						break;
					}
				}
			}
			var genes = '<ul>';
            d3.selectAll("path").filter(function(e, j) { return !(typeof e === "number") && d.join() == e.family.join(); }).each(function(f) {
				genes += '<li><a href="'+feature_link+f.id+'/">'+f.name+'</a>: '+f.fmin+' - '+f.fmax+'</li>';
			});
			genes += '</ul>';
			$("#contextcontent").html(fams.join()+genes);
		});

    legend.append("rect")
        .attr("x", w-18)
        .attr("y", top_pad-10)
        .attr("width", 18)
        .attr("height", rect_h)
        .style("fill", color);

    legend.append("text")
        .attr("x", w-24)
        .attr("y", top_pad+1)
        .attr("dy", ".35em")
        .style("text-anchor", "end")
        .text(function(d) {
            var fams = []
            for( i = 0; i < context_data.families.length; i++) {
                for( j = 0; j < d.length; j++ ) {
                    if( context_data.families[i].id == d[j] ) {
                        fams.push( context_data.families[i].name );
                    }
                }
            }
            return fams.join();
        });
//});

// add tooltips
function tip_gene(d) {
    svg.append("text")
    .attr("class", "tip")
    .attr("transform", "translate("+(x(d.x)+3)+","+(y(d.y)-16)+") rotate(-45)")
    .attr("text-anchor", "left")
    .html(d.name+": "+d.fmin+" - "+d.fmax);
}

function tip_rail_on_track(d) {
    var rail = d3.select(this);
    svg.append("text")
    .attr("class", "tip")
    .attr("transform", "translate("+(parseFloat(rail.attr("x1"))+((parseFloat(rail.attr("x2"))-parseFloat(rail.attr("x1")))/2))+","+(parseFloat(rail.attr("y1"))+10)+") rotate(45)")
    .attr("text-anchor", "right")
    .text(d);
}

// fade tracks
function track_fade(s) {
    s.style("opacity", .1);
}

// unfade the tracks
function track_unfade(s) {
    s.style("opacity", 1);
}

// draw a line between the given gene and it's left neighbor
function draw_line(d) {
    d3.selectAll("path")
    .filter(function(e, j) { return e.x == d.x-1 && e.y == d.y; })
    .each(function(e) {
        svg.append("line")
        .attr("class", "track")
        .attr("x1", x(e.x))
        .attr("x2", x(d.x))
        .attr("y1", y(d.y))
        .attr("y2", y(d.y))
        .data(function() {
			if( d.fmin > e.fmax ) {
				return [d.fmin-e.fmax];
			}
			return [e.fmin-d.fmax];
		})
        .moveToBack();
    });
}

